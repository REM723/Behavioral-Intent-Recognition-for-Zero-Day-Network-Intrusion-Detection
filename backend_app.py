"""
SIZDS - Secure Intelligent Zero-Day Detection System
Backend API Server
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import threading
import time
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import pickle
import os

app = Flask(__name__)
CORS(app)

# Global state
system_state = {
    'running': False,
    'flows_analyzed': 0,
    'threats_detected': 0,
    'false_positives': 0,
    'trust_score': 95,
    'alerts': [],
    'models_status': {},
    'network_stats': {
        'packets_per_sec': 0,
        'data_per_sec': 0,
        'cpu_usage': 0
    },
    'intent_rates': {
        'reconnaissance': 0,
        'lateral_movement': 0,
        'exfiltration': 0,
        'encryption': 0,
        'persistence': 0,
        'denial': 0,
        'exploitation': 0
    }
}

# Sample alerts for demo
SAMPLE_ALERTS = [
    {
        'id': 'ALT-001',
        'type': 'EXFILTRATION',
        'title': 'Suspicious Data Transfer Detected',
        'confidence': 87,
        'description': '5.2 GB outbound transfer to unknown external IP',
        'process': 'chrome.exe',
        'destination': '203.0.113.45',
        'duration': '47 minutes',
        'models': [
            {'name': 'RF Exfiltration', 'score': 87},
            {'name': 'XGBoost', 'score': 89},
            {'name': 'Neural Network', 'score': 91},
            {'name': 'Isolation Forest', 'score': 0.72}
        ],
        'features': [
            'bytes_uploaded: 5200 MB (normal: 4.5 MB) - Z-score: 42.3',
            'upload_download_ratio: 0.98 (normal: 0.1) - Z-score: 15.6',
            'duration: 2820 sec (normal: 144 sec) - Z-score: 32.1',
            'external_destination: unknown IP',
            'timing: 2:23 AM (unusual hours)'
        ],
        'status': 'BLOCKED',
        'action': 'Destination IP blocked, process network access limited',
        'timestamp': None
    },
    {
        'id': 'ALT-002',
        'type': 'ENCRYPTION',
        'title': 'Ransomware Activity Detected',
        'confidence': 88,
        'description': 'Suspicious file access pattern + SMB activity on multiple shares',
        'process': 'ransomware.exe',
        'destination': 'Internal SMB (445)',
        'duration': '5 minutes',
        'models': [
            {'name': 'RF Encryption', 'score': 88},
            {'name': 'XGBoost', 'score': 92},
            {'name': 'Neural Network', 'score': 94}
        ],
        'features': [
            'smb_flows: 500 (normal: 5) - Z-score: 28.4',
            'file_access_variance: 0.89 (abnormal)',
            'c2_communication: detected',
            'network_isolation: active'
        ],
        'status': 'BLOCKED',
        'action': 'Process terminated, SMB ports blocked, files quarantined',
        'timestamp': None
    },
    {
        'id': 'ALT-003',
        'type': 'RECONNAISSANCE',
        'title': 'Network Scanning Detected',
        'confidence': 91,
        'description': '150 unique IPs probed, 200 unique ports scanned',
        'process': 'nmap.exe',
        'destination': 'Multiple internal IPs',
        'duration': '12 minutes',
        'models': [
            {'name': 'RF Reconnaissance', 'score': 91},
            {'name': 'Isolation Forest', 'score': 0.85}
        ],
        'features': [
            'unique_ips: 150 (normal: 5) - Z-score: 45.2',
            'unique_ports: 200 (normal: 1-3) - Z-score: 38.9',
            'failed_connection_ratio: 0.70',
            'low_data_volume: 128 KB'
        ],
        'status': 'BLOCKED',
        'action': 'Rate limiting applied, connection attempts blocked',
        'timestamp': None
    }
]

# ===== INITIALIZATION =====

def init_models():
    """Initialize all ML models"""
    system_state['models_status'] = {
        'rf_reconnaissance': {'status': 'loaded', 'accuracy': 87, 'latency_ms': 12},
        'rf_lateral_movement': {'status': 'loaded', 'accuracy': 92, 'latency_ms': 14},
        'rf_exfiltration': {'status': 'loaded', 'accuracy': 95, 'latency_ms': 11},
        'rf_encryption': {'status': 'loaded', 'accuracy': 89, 'latency_ms': 13},
        'rf_persistence': {'status': 'loaded', 'accuracy': 84, 'latency_ms': 15},
        'rf_denial': {'status': 'loaded', 'accuracy': 91, 'latency_ms': 12},
        'rf_exploitation': {'status': 'loaded', 'accuracy': 88, 'latency_ms': 13},
        'isolation_forest': {'status': 'loaded', 'accuracy': 85, 'latency_ms': 10},
        'autoencoder': {'status': 'loaded', 'accuracy': 83, 'latency_ms': 18},
        'xgboost': {'status': 'loaded', 'accuracy': 96, 'latency_ms': 16},
        'neural_network': {'status': 'loaded', 'accuracy': 94, 'latency_ms': 25},
        'zscore_baseline': {'status': 'loaded', 'accuracy': 72, 'latency_ms': 5},
        'ensemble': {'status': 'loaded', 'accuracy': 97, 'latency_ms': 15}
    }

def simulate_network_traffic():
    """Simulate real network traffic"""
    while system_state['running']:
        # Simulate packets per second
        system_state['network_stats']['packets_per_sec'] = np.random.randint(1000, 8000)
        
        # Simulate data per second (MB)
        system_state['network_stats']['data_per_sec'] = round(np.random.uniform(5, 100), 2)
        
        # Simulate CPU usage
        system_state['network_stats']['cpu_usage'] = np.random.randint(15, 65)
        
        # Simulate intent detection rates
        for intent in system_state['intent_rates']:
            system_state['intent_rates'][intent] = np.random.randint(0, 30)
        
        # Random alert generation (30% chance)
        if np.random.random() > 0.7 and len(system_state['alerts']) < 50:
            alert = SAMPLE_ALERTS[np.random.randint(0, len(SAMPLE_ALERTS))].copy()
            alert['timestamp'] = datetime.now().isoformat()
            system_state['alerts'].insert(0, alert)
            system_state['threats_detected'] += 1
        
        # Update flows analyzed
        system_state['flows_analyzed'] += np.random.randint(50, 150)
        
        # Simulate random false positives
        if np.random.random() > 0.9:
            system_state['false_positives'] += 1
        
        # Adjust trust score (gradually decreases when alerts detected)
        if system_state['threats_detected'] > 0:
            system_state['trust_score'] = max(system_state['trust_score'] - np.random.randint(0, 3), 70)
        
        time.sleep(2)

# ===== ROUTES =====

@app.route('/api/health', methods=['GET'])
def health():
    """System health check"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'models_running': len(system_state['models_status'])
    })

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start system monitoring"""
    if not system_state['running']:
        system_state['running'] = True
        
        # Start traffic simulation in background thread
        thread = threading.Thread(target=simulate_network_traffic, daemon=True)
        thread.start()
        
        return jsonify({'status': 'started', 'message': 'Monitoring started'})
    return jsonify({'status': 'already_running'})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop system monitoring"""
    system_state['running'] = False
    return jsonify({'status': 'stopped', 'message': 'Monitoring stopped'})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    return jsonify({
        'flows_analyzed': system_state['flows_analyzed'],
        'threats_detected': system_state['threats_detected'],
        'false_positives': system_state['false_positives'],
        'trust_score': system_state['trust_score'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/network-stats', methods=['GET'])
def get_network_stats():
    """Get network traffic statistics"""
    return jsonify({
        'packets_per_sec': system_state['network_stats']['packets_per_sec'],
        'data_per_sec': system_state['network_stats']['data_per_sec'],
        'cpu_usage': system_state['network_stats']['cpu_usage'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/intent-rates', methods=['GET'])
def get_intent_rates():
    """Get attack intent detection rates"""
    return jsonify(system_state['intent_rates'])

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get list of alerts"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'total': len(system_state['alerts']),
        'alerts': system_state['alerts'][:limit]
    })

@app.route('/api/alerts/<alert_id>', methods=['GET'])
def get_alert_details(alert_id):
    """Get detailed alert information"""
    for alert in system_state['alerts']:
        if alert['id'] == alert_id:
            return jsonify(alert)
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/models/status', methods=['GET'])
def get_models_status():
    """Get all models status"""
    return jsonify(system_state['models_status'])

@app.route('/api/models/<model_name>/accuracy', methods=['GET'])
def get_model_accuracy(model_name):
    """Get specific model accuracy"""
    if model_name in system_state['models_status']:
        return jsonify(system_state['models_status'][model_name])
    return jsonify({'error': 'Model not found'}), 404

@app.route('/api/analytics/detection-rate', methods=['GET'])
def get_detection_rate():
    """Get detection rate analytics"""
    if system_state['flows_analyzed'] == 0:
        detection_rate = 0
    else:
        detection_rate = (system_state['threats_detected'] / system_state['flows_analyzed']) * 100
    
    return jsonify({
        'detection_rate': round(detection_rate, 2),
        'flows_analyzed': system_state['flows_analyzed'],
        'threats_detected': system_state['threats_detected']
    })

@app.route('/api/analytics/false-positives', methods=['GET'])
def get_false_positive_rate():
    """Get false positive rate"""
    if system_state['flows_analyzed'] == 0:
        fp_rate = 0
    else:
        fp_rate = (system_state['false_positives'] / system_state['flows_analyzed']) * 100
    
    return jsonify({
        'false_positive_rate': round(fp_rate, 2),
        'false_positives': system_state['false_positives'],
        'flows_analyzed': system_state['flows_analyzed']
    })

@app.route('/api/block', methods=['POST'])
def block_threat():
    """Block a threat (IP, process, etc.)"""
    data = request.json
    threat_id = data.get('threat_id')
    threat_type = data.get('type')  # 'ip', 'process', 'domain'
    target = data.get('target')
    
    return jsonify({
        'status': 'blocked',
        'threat_id': threat_id,
        'type': threat_type,
        'target': target,
        'blocked_at': datetime.now().isoformat(),
        'message': f'{threat_type.upper()} {target} has been blocked'
    })

@app.route('/api/quarantine', methods=['POST'])
def quarantine_process():
    """Quarantine a malicious process"""
    data = request.json
    process_name = data.get('process')
    pid = data.get('pid')
    
    return jsonify({
        'status': 'quarantined',
        'process': process_name,
        'pid': pid,
        'quarantined_at': datetime.now().isoformat(),
        'message': f'Process {process_name} has been quarantined'
    })

@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset all metrics"""
    system_state['flows_analyzed'] = 0
    system_state['threats_detected'] = 0
    system_state['false_positives'] = 0
    system_state['trust_score'] = 95
    system_state['alerts'] = []
    
    return jsonify({'status': 'reset', 'message': 'System metrics reset'})

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

# ===== MAIN =====

if __name__ == '__main__':
    init_models()
    app.run(debug=True, host='0.0.0.0', port=5001)
