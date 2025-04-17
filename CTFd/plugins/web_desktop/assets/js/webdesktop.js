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
    // Log the launch attempt
    debugLog(`Launching desktop with template ID: ${templateId}`);

    // Show loading overlay with enhanced feedback
    showLoading('Launching desktop environment...');

    // Update status messages during loading
    const messages = [
        'Initializing...',
        'Creating container...',
        'Allocating resources...',
        'Setting up environment...',
        'Configuring network...',
        'Starting desktop services...',
        'Preparing user interface...'
    ];

    let messageIndex = 0;
    const statusElement = document.getElementById('loading-status');
    const progressBar = document.getElementById('loading-progress-bar');

    // Update status message every 3 seconds
    const messageInterval = setInterval(() => {
        if (statusElement) {
            messageIndex = (messageIndex + 1) % messages.length;
            statusElement.textContent = messages[messageIndex];
            debugLog(`Status update: ${messages[messageIndex]}`);
        }

        // Update progress bar if it exists
        if (progressBar) {
            const currentWidth = parseInt(progressBar.style.width) || 0;
            if (currentWidth < 90) { // Cap at 90% until success
                progressBar.style.width = (currentWidth + 10) + '%';
                debugLog(`Progress update: ${progressBar.style.width}`);
            }
        }
    }, 3000);

    // Set up periodic status checks to detect when container is ready
    let statusCheckCount = 0;
    const maxStatusChecks = 30; // Maximum number of status checks

    const statusCheckInterval = setInterval(() => {
        // Only check if we're still loading
        if (window.isLoadingDesktop) {
            statusCheckCount++;
            debugLog(`Periodic status check #${statusCheckCount}`);

            fetch('/api/v1/plugins/webdesktop/container/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                debugLog(`Status check response: ${JSON.stringify(data)}`);

                // If we have a container and it's running, redirect
                if (data && data.container && data.container.status === 'running') {
                    debugLog('Container is ready! Redirecting...');

                    // Clear intervals and timeouts
                    clearInterval(statusCheckInterval);
                    clearInterval(messageInterval);
                    clearTimeout(loadingTimeout);

                    // Update progress to 100%
                    if (progressBar) {
                        progressBar.style.width = '100%';
                    }

                    // Update status message
                    if (statusElement) {
                        statusElement.textContent = 'Desktop ready! Redirecting...';
                    }

                    // Reload the page after a short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                }

                // If we've reached the maximum number of checks, stop checking
                if (statusCheckCount >= maxStatusChecks) {
                    debugLog('Maximum status checks reached, stopping periodic checks');
                    clearInterval(statusCheckInterval);
                }
            })
            .catch(error => {
                debugLog(`Error in status check: ${error}`);

                // If we've reached the maximum number of checks, stop checking
                if (statusCheckCount >= maxStatusChecks) {
                    clearInterval(statusCheckInterval);
                }
            });
        } else {
            // If we're no longer loading, stop checking
            clearInterval(statusCheckInterval);
        }
    }, 5000); // Check every 5 seconds

    // Set a timeout to detect if we're stuck
    const loadingTimeout = setTimeout(() => {
        // Check if we're still loading
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay && loadingOverlay.style.display !== 'none') {
            debugLog('TIMEOUT: Desktop launch is taking longer than expected');

            // Clear the intervals
            clearInterval(messageInterval);
            clearInterval(statusCheckInterval);

            // Show error message
            if (statusElement) {
                statusElement.textContent = 'Launch timed out. The server might be busy.';
                statusElement.style.color = '#ff6b6b';
            }

            // Add retry button
            const retryButton = document.createElement('button');
            retryButton.className = 'btn btn-primary mt-3';
            retryButton.innerHTML = '<i class="fas fa-sync"></i> Retry';
            retryButton.onclick = function() {
                debugLog('Retry button clicked');
                // Hide the loading overlay
                hideLoading();
                // Try again
                setTimeout(() => launchDesktop(templateId), 500);
            };

            // Add reload button
            const reloadButton = document.createElement('button');
            reloadButton.className = 'btn btn-secondary mt-3 ml-2';
            reloadButton.innerHTML = '<i class="fas fa-redo"></i> Reload Page';
            reloadButton.onclick = function() {
                debugLog('Reload button clicked');
                window.location.reload();
            };

            // Add buttons to the loading overlay
            if (loadingOverlay) {
                const buttonContainer = document.createElement('div');
                buttonContainer.className = 'mt-4';
                buttonContainer.appendChild(retryButton);
                buttonContainer.appendChild(reloadButton);
                loadingOverlay.appendChild(buttonContainer);
            }

            // Add a check container status button for admins
            const debugLogElement = document.getElementById('debug-log');
            if (debugLogElement) {
                const checkStatusButton = document.createElement('button');
                checkStatusButton.className = 'btn btn-info mt-3 ml-2';
                checkStatusButton.innerHTML = '<i class="fas fa-search"></i> Check Status';
                checkStatusButton.onclick = function() {
                    debugLog('Checking container status...');
                    fetch('/api/v1/plugins/webdesktop/container/status', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        debugLog(`Container status response: ${JSON.stringify(data)}`);
                    })
                    .catch(error => {
                        debugLog(`Error checking status: ${error}`);
                    });
                };
                buttonContainer.appendChild(checkStatusButton);
            }
        }
    }, 45000); // 45 second timeout

    debugLog('Sending API request to create container...');
    fetch('/api/v1/plugins/webdesktop/container', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify({ template_id: templateId })
    })
    .then(response => {
        debugLog(`API response status: ${response.status}`);
        return response.json().catch(error => {
            debugLog(`Error parsing JSON: ${error}`);
            return { success: false, message: 'Invalid server response' };
        });
    })
    .then(data => {
        // Clear the intervals and timeouts
        clearInterval(messageInterval);
        clearInterval(statusCheckInterval);
        clearTimeout(loadingTimeout);

        debugLog(`API response data: ${JSON.stringify(data)}`);
        if (data.success) {
            debugLog('Container creation request successful, waiting for container to start');

            // Update progress to 80%
            if (progressBar) {
                progressBar.style.width = '80%';
            }

            // Update status message
            if (statusElement) {
                statusElement.textContent = 'Container created! Starting desktop services...';
            }

            // Start a new status check to wait for the container to be ready
            let readyCheckCount = 0;
            const maxReadyChecks = 12; // Check for up to 1 minute (5s * 12)

            const readyCheckInterval = setInterval(() => {
                readyCheckCount++;
                debugLog(`Ready check #${readyCheckCount}`);

                fetch('/api/v1/plugins/webdesktop/container/status', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(statusData => {
                    debugLog(`Ready check response: ${JSON.stringify(statusData)}`);

                    // If we have a container and it's running, redirect
                    if (statusData && statusData.container && statusData.container.status === 'running') {
                        debugLog('Container is ready! Redirecting...');

                        // Clear interval
                        clearInterval(readyCheckInterval);

                        // Update progress to 100%
                        if (progressBar) {
                            progressBar.style.width = '100%';
                        }

                        // Update status message
                        if (statusElement) {
                            statusElement.textContent = 'Desktop ready! Redirecting...';
                        }

                        // Reload the page after a short delay
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    } else if (readyCheckCount >= maxReadyChecks) {
                        // If we've reached the maximum number of checks, just reload
                        debugLog('Maximum ready checks reached, reloading page');
                        clearInterval(readyCheckInterval);
                        window.location.reload();
                    }
                })
                .catch(error => {
                    debugLog(`Error in ready check: ${error}`);

                    // If we've reached the maximum number of checks, just reload
                    if (readyCheckCount >= maxReadyChecks) {
                        clearInterval(readyCheckInterval);
                        window.location.reload();
                    }
                });
            }, 5000); // Check every 5 seconds
        } else {
            debugLog(`Container creation failed: ${data.message}`);
            hideLoading();
            showAlert('danger', `Error launching desktop: ${data.message}`);
        }
    })
    .catch(error => {
        // Clear the intervals and timeouts
        clearInterval(messageInterval);
        clearInterval(statusCheckInterval);
        clearTimeout(loadingTimeout);

        debugLog(`API request error: ${error}`);
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

    debugLog('Loading container status...');

    fetch('/api/v1/plugins/webdesktop/container/status', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        debugLog(`Container status response code: ${response.status}`);
        return response.json().catch(error => {
            debugLog(`Error parsing container status JSON: ${error}`);
            return { success: false, message: 'Invalid server response' };
        });
    })
    .then(data => {
        debugLog(`Container status data: ${JSON.stringify(data)}`);

        if (data && data.container) {
            debugLog(`Container status: ${data.container.status}`);

            // Update status badge
            const statusBadge = document.getElementById('status-badge');
            if (statusBadge) {
                statusBadge.textContent = data.container.status;
                statusBadge.className = 'status-badge';

                if (data.container.status === 'running') {
                    statusBadge.classList.add('status-running');
                    debugLog('Container is running, updating UI');

                    // Enable iframe if it exists
                    const desktopIframe = document.getElementById('desktop-iframe');
                    if (desktopIframe) {
                        debugLog(`Setting iframe src to: ${data.container.access_url}`);
                        desktopIframe.src = data.container.access_url;
                    }
                } else if (data.container.status === 'starting') {
                    statusBadge.classList.add('status-starting');
                    debugLog('Container is starting, will check again in 5 seconds');

                    // Check again in 5 seconds
                    setTimeout(checkContainerStatus, 5000);
                } else {
                    statusBadge.classList.add('status-stopped');
                    debugLog(`Container is in state: ${data.container.status}`);
                }
            }

            // Update remaining time with seconds
            const timeRemaining = document.getElementById('time-remaining');
            if (timeRemaining && data.container.expire_date) {
                const expireDate = new Date(data.container.expire_date);
                const now = new Date();
                const diffMs = expireDate - now;
                const diffSeconds = Math.floor(diffMs / 1000);

                debugLog(`Container expires in ${diffSeconds} seconds`);

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
                    debugLog('Container is expiring soon');
                }
            }

            // Update container info
            const containerInfo = document.getElementById('container-info');
            if (containerInfo) {
                containerInfo.style.display = 'block';
                debugLog('Showing container info section');
            }

            // Update direct launch URL
            const directLaunchBtn = document.getElementById('direct-launch-btn');
            if (directLaunchBtn && data.container.access_url) {
                debugLog(`Setting direct launch URL to: ${data.container.access_url}`);
                directLaunchBtn.setAttribute('data-url', data.container.access_url);
            }

            // If we were previously showing a loading screen, hide it
            if (window.isLoadingDesktop) {
                debugLog('Container is ready, hiding loading screen');
                hideLoading();
            }
        } else {
            debugLog('No container running, showing template selection');

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

            // If we were previously showing a loading screen, hide it
            if (window.isLoadingDesktop) {
                debugLog('No container found but loading screen was active, hiding it');
                hideLoading();
                showAlert('warning', 'Container creation may have failed. Please try again.');
            }
        }
    })
    .catch(error => {
        debugLog(`Error checking container status: ${error}`);

        // If we were previously showing a loading screen, hide it
        if (window.isLoadingDesktop) {
            debugLog('Error occurred while loading screen was active, hiding it');
            hideLoading();
            showAlert('danger', 'Error checking container status. Please try again.');
        }
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

    // Also log to debug console
    debugLog(`Alert (${type}): ${message}`);
}

// Debug logging function
function debugLog(message) {
    // Log to browser console
    console.log(message);

    // If debug log element exists (admin only), append message there
    const debugLogElement = document.getElementById('debug-log');
    if (debugLogElement) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${message}`;
        debugLogElement.appendChild(logEntry);

        // Scroll to bottom
        debugLogElement.scrollTop = debugLogElement.scrollHeight;
    }
}

function showLoading(message) {
    let loadingOverlay = document.getElementById('loading-overlay');

    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.style.position = 'fixed';
        loadingOverlay.style.top = '0';
        loadingOverlay.style.left = '0';
        loadingOverlay.style.width = '100%';
        loadingOverlay.style.height = '100%';
        loadingOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
        loadingOverlay.style.zIndex = '9999';
        loadingOverlay.style.display = 'flex';
        loadingOverlay.style.justifyContent = 'center';
        loadingOverlay.style.alignItems = 'center';
        loadingOverlay.style.flexDirection = 'column';

        // Create spinner
        const spinner = document.createElement('div');
        spinner.className = 'wd-challenge-spinner';
        spinner.style.display = 'inline-block';
        spinner.style.width = '100px';
        spinner.style.height = '100px';
        spinner.style.border = '6px solid rgba(255, 255, 255, 0.2)';
        spinner.style.borderRadius = '50%';
        spinner.style.borderTopColor = '#007bff';
        spinner.style.animation = 'challenge-spin 1s ease-in-out infinite';
        spinner.style.marginBottom = '25px';

        // Create main text
        const loadingText = document.createElement('div');
        loadingText.id = 'loading-text';
        loadingText.className = 'wd-challenge-text';
        loadingText.style.color = '#fff';
        loadingText.style.fontSize = '24px';
        loadingText.style.marginBottom = '25px';
        loadingText.style.fontWeight = '600';

        // Create status text
        const statusText = document.createElement('div');
        statusText.id = 'loading-status';
        statusText.className = 'wd-challenge-status';
        statusText.style.color = '#6fc2ff';
        statusText.style.fontSize = '18px';
        statusText.style.marginBottom = '25px';
        statusText.textContent = 'Initializing...';

        // Create progress container
        const progressContainer = document.createElement('div');
        progressContainer.className = 'wd-progress-container mt-3';
        progressContainer.style.width = '350px';
        progressContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
        progressContainer.style.borderRadius = '10px';
        progressContainer.style.overflow = 'hidden';
        progressContainer.style.margin = '0 auto';

        // Create progress bar
        const progressBar = document.createElement('div');
        progressBar.id = 'loading-progress-bar';
        progressBar.className = 'wd-progress-bar';
        progressBar.style.height = '10px';
        progressBar.style.width = '0%';
        progressBar.style.backgroundColor = '#007bff';
        progressBar.style.borderRadius = '10px';
        progressBar.style.backgroundImage = 'linear-gradient(45deg, rgba(255, 255, 255, 0.2) 25%, transparent 25%, transparent 50%, rgba(255, 255, 255, 0.2) 50%, rgba(255, 255, 255, 0.2) 75%, transparent 75%, transparent)';
        progressBar.style.backgroundSize = '30px 30px';
        progressBar.style.animation = 'wd-progress-stripes 2s linear infinite';

        // Add elements to the overlay
        progressContainer.appendChild(progressBar);
        loadingOverlay.appendChild(spinner);
        loadingOverlay.appendChild(loadingText);
        loadingOverlay.appendChild(statusText);
        loadingOverlay.appendChild(progressContainer);

        // Add to document
        document.body.appendChild(loadingOverlay);
    }

    // Set the loading message
    const loadingTextElement = document.getElementById('loading-text');
    if (loadingTextElement) {
        loadingTextElement.textContent = message || 'Loading...';
    }

    // Reset progress bar
    const progressBar = document.getElementById('loading-progress-bar');
    if (progressBar) {
        progressBar.style.width = '10%'; // Start at 10%
    }

    // Show the overlay
    loadingOverlay.style.display = 'flex';

    // Set a flag to indicate we're loading a desktop
    window.isLoadingDesktop = true;

    // Log for debugging
    console.log('Loading overlay displayed with message:', message);
}

function hideLoading() {
    // Clear the loading desktop flag
    window.isLoadingDesktop = false;

    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        // Add fade-out effect
        loadingOverlay.style.transition = 'opacity 0.5s';
        loadingOverlay.style.opacity = '0';

        // Hide after animation completes
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
            loadingOverlay.style.opacity = '1';
            loadingOverlay.style.transition = '';

            // Reset progress bar
            const progressBar = document.getElementById('loading-progress-bar');
            if (progressBar) {
                progressBar.style.width = '0%';
            }

            // Reset status text
            const statusText = document.getElementById('loading-status');
            if (statusText) {
                statusText.textContent = 'Initializing...';
                statusText.style.color = '#6fc2ff';
            }

            // Remove any added buttons
            const buttonContainer = loadingOverlay.querySelector('.mt-4');
            if (buttonContainer) {
                loadingOverlay.removeChild(buttonContainer);
            }
        }, 500);

        console.log('Loading overlay hidden');
    }
}