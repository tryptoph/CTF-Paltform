// Web Desktop Plugin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize elements only if they exist
    const launchButtons = document.querySelectorAll('.launch-desktop-btn');
    if (launchButtons.length > 0) {
        launchButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const templateId = this.getAttribute('data-template-id');
                launchDesktop(templateId);
            });
        });
    }

    // Direct launch button
    const directLaunchBtn = document.getElementById('direct-launch-btn');
    if (directLaunchBtn) {
        directLaunchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            if (url) {
                window.open(url, '_blank');
            }
        });
    }

    // Destroy button
    const destroyBtn = document.getElementById('destroy-desktop-btn');
    if (destroyBtn) {
        destroyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to destroy this desktop? All unsaved data will be lost.')) {
                destroyDesktop();
            }
        });
    }

    // Renew button
    const renewBtn = document.getElementById('renew-desktop-btn');
    if (renewBtn) {
        renewBtn.addEventListener('click', function(e) {
            e.preventDefault();
            renewDesktop();
        });
    }

    // Check container status
    checkContainerStatus();
});

// Launch a new desktop
function launchDesktop(templateId) {
    // Show loading overlay
    showLoading('Launching desktop environment...');

    fetch('/api/v1/plugins/webdesktop/container', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify({ template_id: templateId })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Launch response:', data);
        if (data.success) {
            // Reload the page to show the running container
            window.location.reload();
        } else {
            hideLoading();
            showAlert('danger', `Error launching desktop: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showAlert('danger', 'Error launching desktop. Please try again later.');
    });
}

// Destroy the current desktop
function destroyDesktop() {
    showLoading('Destroying desktop environment...');

    fetch('/api/v1/plugins/webdesktop/container', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Destroy response:', data);
        if (data.success) {
            // Reload the page to show the desktop selection
            window.location.reload();
        } else {
            hideLoading();
            showAlert('danger', `Error destroying desktop: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showAlert('danger', 'Error destroying desktop. Please try again later.');
    });
}

// Renew the current desktop time
function renewDesktop() {
    showLoading('Renewing desktop time...');

    fetch('/api/v1/plugins/webdesktop/container/renew', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Renew response:', data);
        hideLoading();
        if (data.success) {
            showAlert('success', 'Desktop time renewed successfully!');
            // Refresh container information
            setTimeout(function() {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('danger', `Error renewing desktop: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showAlert('danger', 'Error renewing desktop. Please try again later.');
    });
}

// Check the status of the current container
function checkContainerStatus() {
    const statusContainer = document.getElementById('container-status');
    if (!statusContainer) return;

    console.log('Loading container status...');

    fetch('/api/v1/plugins/webdesktop/container/status', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('Container status response:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Container status data:', data);

        if (data && data.container) {
            console.log('Showing container status:', data.container.status, data);

            // Update status badge
            const statusBadge = document.getElementById('status-badge');
            if (statusBadge) {
                statusBadge.textContent = data.container.status;
                statusBadge.className = 'status-badge';

                if (data.container.status === 'running') {
                    statusBadge.classList.add('status-running');

                    // Enable iframe if it exists
                    const desktopIframe = document.getElementById('desktop-iframe');
                    if (desktopIframe) {
                        desktopIframe.src = data.container.access_url;
                    }
                } else if (data.container.status === 'starting') {
                    statusBadge.classList.add('status-starting');

                    // Check again in 5 seconds
                    setTimeout(checkContainerStatus, 5000);
                } else {
                    statusBadge.classList.add('status-stopped');
                }
            }

            // Update remaining time with seconds
            const timeRemaining = document.getElementById('time-remaining');
            if (timeRemaining && data.container.expire_date) {
                const expireDate = new Date(data.container.expire_date);
                const now = new Date();
                const diffMs = expireDate - now;
                const diffSeconds = Math.floor(diffMs / 1000);

                if (diffSeconds > 0) {
                    // Calculate hours, minutes, seconds
                    const hours = Math.floor(diffSeconds / 3600);
                    const minutes = Math.floor((diffSeconds % 3600) / 60);
                    const seconds = diffSeconds % 60;

                    // Format with hours, minutes, and seconds
                    if (hours > 0) {
                        timeRemaining.textContent = `${hours}h ${minutes}m ${seconds}s`;
                    } else {
                        timeRemaining.textContent = `${minutes}m ${seconds}s`;
                    }
                } else {
                    timeRemaining.textContent = 'Expiring soon';
                }
            }

            // Update container info
            const containerInfo = document.getElementById('container-info');
            if (containerInfo) {
                containerInfo.style.display = 'block';
            }

            // Update direct launch URL
            const directLaunchBtn = document.getElementById('direct-launch-btn');
            if (directLaunchBtn && data.container.access_url) {
                directLaunchBtn.setAttribute('data-url', data.container.access_url);
            }
        } else {
            console.log('No container running');

            // Hide container info
            const containerInfo = document.getElementById('container-info');
            if (containerInfo) {
                containerInfo.style.display = 'none';
            }

            // Show template selection
            const templateSelection = document.getElementById('template-selection');
            if (templateSelection) {
                templateSelection.style.display = 'block';
            }
        }
    })
    .catch(error => {
        console.error('Error checking container status:', error);
    });
}

// Helper functions
function getCSRFToken() {
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    return tokenElement ? tokenElement.getAttribute('content') : '';
}

function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
    `;

    alertContainer.innerHTML = alertHTML;

    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            $(alert).alert('close');
        });
    }, 5000);
}

function showLoading(message) {
    let loadingOverlay = document.getElementById('loading-overlay');

    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.className = 'loading-overlay';

        const spinner = document.createElement('div');
        spinner.className = 'spinner';

        const loadingText = document.createElement('div');
        loadingText.id = 'loading-text';

        loadingOverlay.appendChild(spinner);
        loadingOverlay.appendChild(loadingText);
        document.body.appendChild(loadingOverlay);
    }

    document.getElementById('loading-text').textContent = message || 'Loading...';
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}