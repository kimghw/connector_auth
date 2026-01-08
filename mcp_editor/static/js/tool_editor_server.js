/* Tool Editor Server - MCP Server Control Functions */

// ===== MCP Server Control Functions =====
function serverProfileParam() {
    // Use serverControlProfile for server operations
    return serverControlProfile ? `?profile=${encodeURIComponent(serverControlProfile)}` : '';
}

function populateServerProfileSelector() {
    const select = document.getElementById('serverProfileSelect');
    if (!select) return;

    // Clear existing options except the first placeholder
    select.innerHTML = '<option value="">Select profile...</option>';

    // Add all profiles as options
    profiles.forEach(profile => {
        const option = document.createElement('option');
        option.value = profile;
        option.textContent = profile;
        if (profile === serverControlProfile) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

function onServerProfileChange() {
    const select = document.getElementById('serverProfileSelect');
    if (!select) return;

    serverControlProfile = select.value;
    console.log('Server control profile changed to:', serverControlProfile);

    // Update the profile display in serverInfo
    const profileValue = document.getElementById('profileValue');
    if (profileValue) {
        profileValue.textContent = serverControlProfile || 'default';
    }

    // Check status with new profile
    checkServerStatus();
}

function checkServerStatus() {
    const profileQuery = serverProfileParam();
    fetch(`/api/server/status${profileQuery}`)
        .then(response => response.json())
        .then(data => {
            updateServerStatusUI(data);
        })
        .catch(error => {
            console.error('Error checking server status:', error);
            updateServerStatusUI({ running: false, error: error.message });
        });
}

function updateServerStatusUI(status) {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const btnStart = document.getElementById('btnStart');
    const btnStop = document.getElementById('btnStop');
    const btnRestart = document.getElementById('btnRestart');
    const pidInfo = document.getElementById('pidInfo');
    const pidValue = document.getElementById('pidValue');
    const profileValue = document.getElementById('profileValue');

    if (status.running) {
        // Server is running
        statusIndicator.style.background = '#28a745';
        statusText.textContent = 'Running';
        statusText.style.color = '#28a745';
        btnStart.disabled = true;
        btnStop.disabled = false;
        btnRestart.disabled = false;

        // Show PID info if available
        if (status.pid) {
            pidInfo.style.display = 'block';
            pidValue.textContent = status.pid;
        } else {
            pidInfo.style.display = 'none';
        }
    } else {
        // Server is stopped
        statusIndicator.style.background = '#dc3545';
        statusText.textContent = 'Stopped';
        statusText.style.color = '#dc3545';
        btnStart.disabled = false;
        btnStop.disabled = true;
        btnRestart.disabled = true;
        pidInfo.style.display = 'none';
    }

    // Update profile info
    if (profileValue && status.profile) {
        profileValue.textContent = status.profile;
    }
}

function startServer() {
    const profileQuery = serverProfileParam();
    const btnStart = document.getElementById('btnStart');
    const statusText = document.getElementById('statusText');

    btnStart.disabled = true;
    statusText.textContent = 'Starting...';
    statusText.style.color = '#ffc107';

    fetch(`/api/server/start${profileQuery}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Server started successfully', 'success');
                checkServerStatus();
            } else {
                showToast('Failed to start server: ' + (data.error || 'Unknown error'), 'error');
                btnStart.disabled = false;
                statusText.textContent = 'Stopped';
                statusText.style.color = '#dc3545';
            }
        })
        .catch(error => {
            showToast('Error starting server: ' + error.message, 'error');
            btnStart.disabled = false;
            statusText.textContent = 'Stopped';
            statusText.style.color = '#dc3545';
        });
}

function stopServer() {
    const profileQuery = serverProfileParam();
    const btnStop = document.getElementById('btnStop');
    const statusText = document.getElementById('statusText');

    btnStop.disabled = true;
    statusText.textContent = 'Stopping...';
    statusText.style.color = '#ffc107';

    fetch(`/api/server/stop${profileQuery}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: false })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Server stopped successfully', 'success');
                checkServerStatus();
            } else {
                showToast('Failed to stop server: ' + (data.error || 'Unknown error'), 'error');
                btnStop.disabled = false;
                checkServerStatus();
            }
        })
        .catch(error => {
            showToast('Error stopping server: ' + error.message, 'error');
            btnStop.disabled = false;
            checkServerStatus();
        });
}

function restartServer() {
    const profileQuery = serverProfileParam();
    const btnRestart = document.getElementById('btnRestart');
    const statusText = document.getElementById('statusText');

    btnRestart.disabled = true;
    statusText.textContent = 'Restarting...';
    statusText.style.color = '#ffc107';

    fetch(`/api/server/restart${profileQuery}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Server restarted successfully', 'success');
                checkServerStatus();
            } else {
                showToast('Failed to restart server: ' + (data.error || 'Unknown error'), 'error');
                btnRestart.disabled = false;
                checkServerStatus();
            }
        })
        .catch(error => {
            showToast('Error restarting server: ' + error.message, 'error');
            btnRestart.disabled = false;
            checkServerStatus();
        });
}
// ===== End of MCP Server Control Functions =====
