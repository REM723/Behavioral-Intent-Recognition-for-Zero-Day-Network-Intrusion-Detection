// SIZDS Pro - Dashboard JavaScript
const API_BASE = 'http://localhost:5001/api';

let currentProcess = null;
let currentThreat = null;

// ===== PAGE NAVIGATION =====

function switchPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Remove active from nav buttons
    document.querySelectorAll('.nav-links button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected page
    document.getElementById(pageName).classList.add('active');

    // Add active to nav button
    event.target.classList.add('active');

    // Load page-specific data
    if (pageName === 'overview') {
        loadOverviewData();
    } else if (pageName === 'processes') {
        loadProcessesData();
    } else if (pageName === 'analytics') {
        loadAnalyticsData();
    }
}

// ===== THREAT DETECTION & EXPLANATION =====

const threatDetails = {
    exfil: {
        title: 'Exfiltration - Data Theft Detected',
        type: 'Data Exfiltration',
        confidence: '87%',
        modelsAgree: '4/8 models',
        description: '5.2 GB outbound transfer to unknown external IP detected.',
        features: [
            'bytes_uploaded: 5200 MB (normal: 4.5 MB) - Z-score: 42.3',
            'upload_download_ratio: 0.98 (normal: 0.1) - Z-score: 15.6',
            'duration: 2820 sec (normal: 144 sec) - Z-score: 32.1',
            'external_destination: 203.0.113.45 (unknown IP)',
            'timing: 2:23 AM (unusual hours)'
        ],
        models: ['RF Exfiltration: 87%', 'XGBoost: 89%', 'Neural Network: 91%', 'Isolation Forest: 0.72'],
        whyBlocked: 'Machine learning ensemble detected clear exfiltration behavior. 4 models agreed the unusual upload patterns, large volume, and external destination indicate data theft.',
        action: 'Destination IP blocked, process network access limited'
    },
    encrypt: {
        title: 'Encryption/Ransomware - File Encryption Detected',
        type: 'Ransomware Attack',
        confidence: '92%',
        modelsAgree: '6/8 models',
        description: 'Suspicious file access patterns + SMB activity detected. Indicates ransomware encrypting files.',
        features: [
            'smb_flows: 500 (normal: 5) - Z-score: 28.4',
            'file_access_variance: 0.89 (abnormal pattern)',
            'c2_communication: detected (callback patterns)',
            'network_isolation: active (behavioral signature)'
        ],
        models: ['RF Encryption: 92%', 'XGBoost: 92%', 'Neural Network: 94%', 'Isolation Forest: 0.85'],
        whyBlocked: 'Six models detected ransomware intent through behavioral analysis. The combination of rapid file access, SMB targeting, and C2 patterns is characteristic of encryption malware regardless of specific signature.',
        action: 'Process terminated, SMB ports blocked, files quarantined'
    },
    recon: {
        title: 'Reconnaissance - Network Scanning Detected',
        type: 'Network Reconnaissance',
        confidence: '78%',
        modelsAgree: '3/8 models',
        description: '150 unique IPs probed with 200+ unique ports scanned. Indicates active reconnaissance.',
        features: [
            'unique_ips: 150 (normal: 5) - Z-score: 45.2',
            'unique_ports: 200 (normal: 1-3) - Z-score: 38.9',
            'failed_connection_ratio: 0.70 (very high)',
            'low_data_volume: 128 KB (characteristic of scanning)'
        ],
        models: ['RF Reconnaissance: 78%', 'Isolation Forest: 0.85'],
        whyBlocked: 'Behavioral intent detection identifies reconnaissance behavior. The attacker is probing the network to find vulnerabilities, even though specific attack method is unknown (zero-day).',
        action: 'Rate limiting applied, further scanning blocked'
    }
};

function viewThreat(threatId) {
    const threat = threatDetails[threatId];
    if (!threat) return;

    currentThreat = threat;
    
    const modal = document.getElementById('threatModal');
    const body = document.getElementById('threatModalBody');

    body.innerHTML = `
        <div class="modal-section">
            <div class="modal-section-title">Threat Summary</div>
            <div class="modal-detail">
                <span class="modal-detail-label">Type:</span>
                <span class="modal-detail-value">${threat.type}</span>
            </div>
            <div class="modal-detail">
                <span class="modal-detail-label">Confidence:</span>
                <span class="modal-detail-value">${threat.confidence}</span>
            </div>
            <div class="modal-detail">
                <span class="modal-detail-label">Models Agreeing:</span>
                <span class="modal-detail-value">${threat.modelsAgree}</span>
            </div>
        </div>

        <div class="modal-section">
            <div class="modal-section-title">Description</div>
            <p style="color: var(--gray-300); line-height: 1.6;">${threat.description}</p>
        </div>

        <div class="modal-section">
            <div class="modal-section-title">Key Features That Triggered Detection</div>
            <div style="space: 0.5rem;">
                ${threat.features.map(f => `<div style="color: var(--gray-300); font-size: 0.9rem; padding: 0.5rem 0; border-bottom: 1px solid var(--gray-800);">✓ ${f}</div>`).join('')}
            </div>
        </div>

        <div class="modal-section">
            <div class="modal-section-title">Model Predictions</div>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                ${threat.models.map(m => `<span style="background: var(--gray-800); color: var(--gray-300); padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.85rem;">${m}</span>`).join('')}
            </div>
        </div>

        <div class="modal-section">
            <div class="modal-section-title">Why It Was Detected (Behavioral Intent Analysis)</div>
            <p style="color: var(--gray-300); line-height: 1.6;">${threat.whyBlocked}</p>
            <div style="background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 6px; padding: 1rem; margin-top: 1rem;">
                <strong style="color: var(--green);">✓ Zero-Day Advantage:</strong>
                <p style="color: var(--gray-300); font-size: 0.9rem; margin-top: 0.5rem;">This detection works on unknown malware variants because it identifies WHAT the attacker is doing (intent), not HOW the code looks (signature).</p>
            </div>
        </div>

        <div class="modal-section">
            <div class="modal-section-title">Action Taken</div>
            <p style="color: var(--green);">${threat.action}</p>
        </div>
    `;

    modal.classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ===== PROCESS ISOLATION =====

function viewProcess(processName) {
    const modal = document.getElementById('processModal');
    const body = document.getElementById('processModalBody');

    body.innerHTML = `
        <div class="modal-section">
            <div class="modal-section-title">Process Information</div>
            <div class="modal-detail">
                <span class="modal-detail-label">Name:</span>
                <span class="modal-detail-value">${processName}</span>
            </div>
            <div class="modal-detail">
                <span class="modal-detail-label">Status:</span>
                <span class="modal-detail-value">Running - Normal Behavior</span>
            </div>
        </div>

        <div class="modal-section">
            <div class="modal-section-title">Network Analysis</div>
            <p style="color: var(--gray-300);">Process is using expected network resources for normal operation. No suspicious outbound connections detected.</p>
        </div>
    `;

    modal.classList.add('active');
}

function isolateProcess(processName, pid) {
    currentProcess = { name: processName, pid: pid };
    document.getElementById('isolateModal').classList.add('active');
}

function confirmIsolate() {
    if (!currentProcess) return;

    const isolation = document.getElementById('isolateModal');
    const body = isolation.querySelector('.modal-content > div:nth-child(2)');

    // Show success message
    body.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">✓</div>
            <h3 style="color: var(--green); margin-bottom: 1rem;">Process Isolated Successfully</h3>
            <p style="color: var(--gray-300); margin-bottom: 1.5rem;">
                <strong>${currentProcess.name}</strong> (PID: ${currentProcess.pid}) has been isolated from the network.
            </p>
            <div style="background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 6px; padding: 1rem; margin-bottom: 1.5rem; text-align: left;">
                <strong style="color: var(--green);">Actions Taken:</strong>
                <ul style="color: var(--gray-300); font-size: 0.9rem; margin-top: 0.5rem; list-style: none; padding: 0;">
                    <li>✓ Network access blocked</li>
                    <li>✓ All outbound connections terminated</li>
                    <li>✓ Process monitored for further activity</li>
                    <li>✓ Incident logged (Case: #12345)</li>
                </ul>
            </div>
        </div>
        <button class="btn" onclick="closeModal('isolateModal')" style="width: 100%;">Close</button>
    `;
}

// ===== DATA LOADING =====

function loadOverviewData() {
    updateOverviewStats();
    updateThreats();
}

function loadProcessesData() {
    // Already populated in HTML
}

function loadAnalyticsData() {
    // Already populated in HTML
}

function updateOverviewStats() {
    // Simulate real-time updates
    document.getElementById('totalFlows').textContent = Math.floor(Math.random() * 10000).toLocaleString();
    document.getElementById('threatsDetected').textContent = Math.floor(Math.random() * 10);
    document.getElementById('systemHealth').textContent = (90 + Math.random() * 9).toFixed(0) + '%';
    
    // Update intent rates
    document.getElementById('intent-exfil').textContent = Math.floor(Math.random() * 20) + '%';
    document.getElementById('intent-encrypt').textContent = Math.floor(Math.random() * 15) + '%';
    document.getElementById('intent-recon').textContent = Math.floor(Math.random() * 18) + '%';
    document.getElementById('intent-lateral').textContent = Math.floor(Math.random() * 12) + '%';
    document.getElementById('intent-denial').textContent = Math.floor(Math.random() * 10) + '%';
    document.getElementById('intent-persist').textContent = Math.floor(Math.random() * 8) + '%';
    document.getElementById('intent-exploit').textContent = Math.floor(Math.random() * 14) + '%';
}

function updateThreats() {
    // Already populated in HTML
}

function refreshProcesses() {
    alert('Processes refreshed. System scan in progress...');
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    loadOverviewData();
    
    // Auto-update every 3 seconds
    setInterval(updateOverviewStats, 3000);
});

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal.active');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.classList.remove('active');
        }
    });
});
