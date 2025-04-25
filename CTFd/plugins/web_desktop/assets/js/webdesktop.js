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

    // Destroy button - initially disabled with a delay
    const destroyBtn = document.getElementById('destroy-desktop-btn');
    if (destroyBtn) {
        // Initially disable the button and enable after a delay
        destroyBtn.disabled = true;
        destroyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';

        // Enable after a delay
        setTimeout(() => {
            destroyBtn.disabled = false;
            destroyBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Destroy Desktop';

            // Add click event listener
            destroyBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (confirm('Are you sure you want to destroy this desktop? All unsaved data will be lost.')) {
                    destroyDesktop();
                }
            });
        }, 3000);
    }

    // Renew button - initially disabled with a delay
    const renewBtn = document.getElementById('renew-desktop-btn');
    if (renewBtn) {
        // Initially disable the button and enable after a delay
        renewBtn.disabled = true;
        renewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';

        // Enable after a delay
        setTimeout(() => {
            renewBtn.disabled = false;
            renewBtn.innerHTML = '<i class="fas fa-sync"></i> Renew Desktop';

            // Add click event listener
            renewBtn.addEventListener('click', function(e) {
                e.preventDefault();
                renewDesktop();
            });
        }, 3000);
    }

    // Check container status
    checkContainerStatus();
});

// Launch a new desktop
function launchDesktop(templateId) {
    // Log the launch attempt
    debugLog(`Launching desktop with template ID: ${templateId}`);

    // Show loading overlay
    showLoading('Launching desktop environment...');
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

    // Destroy button - initially disabled with a delay
    const destroyBtn = document.getElementById('destroy-desktop-btn');
    if (destroyBtn) {
        // Initially disable the button and enable after a delay
        destroyBtn.disabled = true;
        destroyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';

        // Enable after a delay
        setTimeout(() => {
            destroyBtn.disabled = false;
            destroyBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Destroy Desktop';

            // Add click event listener
            destroyBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (confirm('Are you sure you want to destroy this desktop? All unsaved data will be lost.')) {
                    destroyDesktop();
                }
            });
        }, 3000);
    }

    // Renew button - initially disabled with a delay
    const renewBtn = document.getElementById('renew-desktop-btn');
    if (renewBtn) {
        // Initially disable the button and enable after a delay
        renewBtn.disabled = true;
        renewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';

        // Enable after a delay
        setTimeout(() => {
            renewBtn.disabled = false;
            renewBtn.innerHTML = '<i class="fas fa-sync"></i> Renew Desktop';

            // Add click event listener
            renewBtn.addEventListener('click', function(e) {
                e.preventDefault();
                renewDesktop();
            });
        }, 3000);
    }

    // Check container status
    checkContainerStatus();
});

// Launch a new desktop
function launchDesktop(templateId) {
    // Log the launch attempt
    debugLog(`Launching desktop with template ID: ${templateId}`);

    // Show loading overlay
    showLoading('Launching desktop environment...');

    // Get elements for updating
    const progressBar = document.getElementById('loading-progress-bar');
    const statusElement = document.getElementById('loading-status');

    // Update progress bar
    const progressInterval = setInterval(() => {
        // Update progress bar if it exists
        if (progressBar) {
            const currentWidth = parseInt(progressBar.style.width) || 0;
            if (currentWidth < 95) { // Cap at 95% until success
                const newWidth = Math.min(95, currentWidth + 20);
                progressBar.style.width = newWidth + '%';

                // Force a reflow to ensure the animation runs
                document.body.offsetHeight;
            }
        }
    }, 500); // Update every 500ms instead of 1000ms

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
                    clearInterval(progressInterval);
                    clearTimeout(loadingTimeout);

                    // Update progress to 100% with !important to override animations
                    if (progressBar) {
                        // Force the progress bar to 100% with !important
                        progressBar.style.cssText += 'width: 100% !important; transition: width 0.5s !important;';
                        // Also set the animation to none to prevent any animation from overriding this
                        progressBar.style.animation = 'none';
                    }

                    // Update status message
                    if (statusElement) {
                        statusElement.textContent = 'Desktop ready! Redirecting...';
                    }

                    // Reload the page after a delay (increased to 3 seconds)
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
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
    }, 8000); // Check every 8 seconds (increased from 5)

    // Set a timeout to detect if we're stuck (increased by 6 seconds total)
    const loadingTimeout = setTimeout(() => {
        // Check if we're still loading
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay && loadingOverlay.style.display !== 'none') {
            debugLog('TIMEOUT: Desktop launch is taking longer than expected');

            // Clear the intervals
            clearInterval(progressInterval);
            clearInterval(statusCheckInterval);

            // Show red progress bar for error
            const simpleProgressBar = document.getElementById('simple-progress-bar');
            const progressText = document.getElementById('progress-percentage');

            if (simpleProgressBar && progressText) {
                // Clear any existing interval
                clearInterval(progressInterval);

                // Animate to 100% with error color
                let errorProgress = currentProgress;
                const errorInterval = setInterval(() => {
                    if (errorProgress < 100) {
                        errorProgress += 2;
                        simpleProgressBar.style.width = errorProgress + '%';
                        progressText.textContent = errorProgress + '%';
                    } else {
                        clearInterval(errorInterval);

                        // Add error effect
                        simpleProgressBar.style.backgroundColor = '#dc3545'; // Red
                        progressText.style.fontWeight = 'bold';
                    }
                }, 50);
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
    }, 51000); // 51 second timeout (increased by 3 more seconds)

    debugLog('Sending API request to create container...');

    // Add a 3-second delay before sending the request to ensure backend has time to initialize
    setTimeout(() => {
        debugLog('Sending delayed container creation request after 3 seconds...');
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
        clearInterval(progressInterval);
        clearInterval(statusCheckInterval);
        clearTimeout(loadingTimeout);

        debugLog(`API response data: ${JSON.stringify(data)}`);
        if (data.success) {
            debugLog('Container creation request successful, waiting for container to start');

            // Update progress to 80
    // Get elements for updating
    const progressBar = document.getElementById('loading-progress-bar');
    const statusElement = document.getElementById('loading-status');

    // Update progress bar
    const progressInterval = setInterval(() => {
        // Update progress bar if it exists
        if (progressBar) {
            const currentWidth = parseInt(progressBar.style.width) || 0;
            if (currentWidth < 95) { // Cap at 95% until success
                const newWidth = Math.min(95, currentWidth + 15);
                progressBar.style.width = newWidth + '%';
            }
        }
    }, 1000);

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
                    clearInterval(progressInterval);
                    clearTimeout(loadingTimeout);

                    // Set progress to 100%
                    targetProgress = 100;

                    // Clear the interval and set progress directly
                    clearInterval(progressInterval);

                    // Get the new progress bar
                    const simpleProgressBar = document.getElementById('simple-progress-bar');
                    const progressText = document.getElementById('progress-percentage');

                    if (simpleProgressBar && progressText) {
                        // Animate to 100% smoothly
                        let completeProgress = currentProgress;
                        const completeInterval = setInterval(() => {
                            if (completeProgress < 100) {
                                completeProgress += 2;
                                simpleProgressBar.style.width = completeProgress + '%';
                                progressText.textContent = completeProgress + '%';
                            } else {
                                clearInterval(completeInterval);

                                // Add success effect
                                simpleProgressBar.style.backgroundColor = '#28a745';
                                progressText.style.fontWeight = 'bold';
                            }
                        }, 50);
                    }

                    // Update status message
                    if (statusElement) {
                        statusElement.textContent = 'Desktop ready! Redirecting...';
                    }

                    // Reload the page after a delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
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
    }, 8000); // Check every 8 seconds (increased from 5)

    // Set a timeout to detect if we're stuck (increased by 6 seconds total)
    const loadingTimeout = setTimeout(() => {
        // Check if we're still loading
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay && loadingOverlay.style.display !== 'none') {
            debugLog('TIMEOUT: Desktop launch is taking longer than expected');

            // Clear the intervals
            clearInterval(progressInterval);
            clearInterval(statusCheckInterval);

            // Show red progress bar for error
            const simpleProgressBar = document.getElementById('simple-progress-bar');
            const progressText = document.getElementById('progress-percentage');

            if (simpleProgressBar && progressText) {
                // Clear any existing interval
                clearInterval(progressInterval);

                // Animate to 100% with error color
                let errorProgress = currentProgress;
                const errorInterval = setInterval(() => {
                    if (errorProgress < 100) {
                        errorProgress += 2;
                        simpleProgressBar.style.width = errorProgress + '%';
                        progressText.textContent = errorProgress + '%';
                    } else {
                        clearInterval(errorInterval);

                        // Add error effect
                        simpleProgressBar.style.backgroundColor = '#dc3545'; // Red
                        progressText.style.fontWeight = 'bold';
                    }
                }, 50);
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
    }, 51000); // 51 second timeout (increased by 3 more seconds)

    debugLog('Sending API request to create container...');

    // Add a 3-second delay before sending the request to ensure backend has time to initialize
    setTimeout(() => {
        debugLog('Sending delayed container creation request after 3 seconds...');
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
        clearInterval(progressInterval);
        clearInterval(statusCheckInterval);
        clearTimeout(loadingTimeout);

        debugLog(`API response data: ${JSON.stringify(data)}`);
        if (data.success) {
            debugLog('Container creation request successful, waiting for container to start');

            // Update progress target
            targetProgress = 80;

            // Update status message
            if (statusElement) {
                statusElement.textContent = 'Container created! Starting desktop services...';
            }

            // Start a new status check to wait for the container to be ready
            let readyCheckCount = 0;
            const maxReadyChecks = 15; // Check for up to 1 minute 15 seconds (5s * 15)

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

                        // Set progress to 100%
                        targetProgress = 100;

                        // Clear the interval and set progress directly
                        clearInterval(progressInterval);

                        // Get the new progress bar
                        const simpleProgressBar = document.getElementById('simple-progress-bar');
                        const progressText = document.getElementById('progress-percentage');

                        if (simpleProgressBar && progressText) {
                            // Animate to 100% smoothly
                            let completeProgress = currentProgress;
                            const completeInterval = setInterval(() => {
                                if (completeProgress < 100) {
                                    completeProgress += 2;
                                    simpleProgressBar.style.width = completeProgress + '%';
                                    progressText.textContent = completeProgress + '%';
                                } else {
                                    clearInterval(completeInterval);

                                    // Add success effect
                                    simpleProgressBar.style.backgroundColor = '#28a745';
                                    progressText.style.fontWeight = 'bold';
                                }
                            }, 50);
                        }

                        // Update status message
                        if (statusElement) {
                            statusElement.textContent = 'Desktop ready! Redirecting...';
                        }

                        // Reload the page after a delay
                        setTimeout(() => {
                            window.location.reload();
                        }, 3000);
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
            }, 8000); // Check every 8 seconds (increased from 5)
        } else {
            debugLog(`Container creation failed: ${data.message}`);
            hideLoading();
            showAlert('danger', `Error launching desktop: ${data.message}`);
        }
    })
    .catch(error => {
        // Clear the intervals and timeouts
        clearInterval(progressInterval);
        clearInterval(statusCheckInterval);
        clearTimeout(loadingTimeout);

        debugLog(`API request error: ${error}`);
        hideLoading();
        showAlert('danger', 'Error launching desktop. Please try again later.');
    });
    }, 3000); // Close the setTimeout with a 3-second delay
}

// Destroy the current desktop
function destroyDesktop() {
    showLoading();

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
    showLoading();

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

                    // Enable iframe if it exists - with a delay to ensure container is fully ready
                    const desktopIframe = document.getElementById('desktop-iframe');
                    if (desktopIframe) {
                        debugLog(`Will set iframe src to: ${data.container.access_url} after 3 second delay`);

                        // Add a delay before setting the iframe src
                        setTimeout(() => {
                            debugLog(`Now setting iframe src to: ${data.container.access_url}`);
                            desktopIframe.src = data.container.access_url;
                        }, 3000);
                    }
                } else if (data.container.status === 'starting') {
                    statusBadge.classList.add('status-starting');
                    debugLog('Container is starting, will check again in 10 seconds');

                    // Check again in 10 seconds (increased from 5)
                    setTimeout(checkContainerStatus, 10000);
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

            // Update direct launch URL - with a delay to ensure it's ready
            const directLaunchBtn = document.getElementById('direct-launch-btn');
            if (directLaunchBtn && data.container.access_url) {
                debugLog(`Setting direct launch URL to: ${data.container.access_url}`);
                directLaunchBtn.setAttribute('data-url', data.container.access_url);

                // Disable the button initially and enable after a delay
                directLaunchBtn.disabled = true;
                directLaunchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';

                setTimeout(() => {
                    debugLog('Enabling direct launch button after delay');
                    directLaunchBtn.disabled = false;
                    directLaunchBtn.innerHTML = '<i class="fas fa-external-link-alt"></i> Open in New Tab';
                }, 3000);
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

// Global variables for progress tracking
let progressInterval = null;
let currentProgress = 0;
let targetProgress = 0;

function showLoading(message) {
    let loadingOverlay = document.getElementById('loading-overlay');

    if (!loadingOverlay) {
        // If the loading overlay doesn't exist, use the one in desktop.html
        console.error('Loading overlay not found - it should be defined in desktop.html');
        return;
    }

    // Reset progress bar
    const progressBar = document.getElementById('simple-progress-bar');
    const progressText = document.getElementById('progress-percentage');

    if (progressBar && progressText) {
        // Reset progress
        currentProgress = 0;
        targetProgress = 20; // Initial target

        // Reset styles
        progressBar.style.width = '0%';
        progressBar.style.backgroundColor = '#28a745'; // Green
        progressText.textContent = '0%';

        // Clear any existing interval
        if (progressInterval) {
            clearInterval(progressInterval);
        }

        // Start progress animation
        progressInterval = setInterval(() => {
            // If we haven't reached target yet, increment
            if (currentProgress < targetProgress) {
                currentProgress += 1;
                progressBar.style.width = currentProgress + '%';
                progressText.textContent = currentProgress + '%';
            }
        }, 100); // Update every 100ms for smooth animation

        // After a delay, set initial progress
        setTimeout(() => {
            targetProgress = 30;
        }, 1000);
    }

    // Update message if provided
    const loadingText = document.getElementById('loading-text');
    if (loadingText && message) {
        loadingText.textContent = message;
    }

    // Show the overlay
    loadingOverlay.style.display = 'flex';

    // Set a flag to indicate we're loading a desktop
    window.isLoadingDesktop = true;
}

function hideLoading() {
    // Clear any progress interval
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }

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
            const progressBar = document.getElementById('simple-progress-bar');
            const progressText = document.getElementById('progress-percentage');

            if (progressBar && progressText) {
                progressBar.style.width = '0%';
                progressBar.style.backgroundColor = '#28a745';
                progressText.textContent = '0%';
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