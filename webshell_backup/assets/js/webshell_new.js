/**
 * WebShell Plugin JavaScript - Rewritten to match CTFd-whale approach
 */

const WebShell = (function() {
    // Private variables
    let config = {
        apiEndpoint: '',
        csrfToken: '',
        isAuthed: false,
        loginUrl: ''
    };

    let state = {
        container: null,
        refreshInterval: null,
        timeRemainingInterval: null
    };

    /**
     * Initialize the WebShell
     * @param {Object} options - Configuration options
     */
    function init(options) {
        // Parse and merge options
        config = {...config, ...options};
        console.log('[WebShell] Initializing with config:', config);

        // Make sure API endpoint is properly set
        if (!config.apiEndpoint.startsWith('/')) {
            config.apiEndpoint = '/' + config.apiEndpoint;
        }
        
        // Show info message for debugging
        showInfo('Initializing WebShell interface...', 2000);
        
        // If user is not authenticated, don't proceed with API calls
        if (!config.isAuthed) {
            console.log('[WebShell] User not authenticated');
            // Show launcher if not disabled
            const launcher = document.getElementById('webshell-launcher');
            if (launcher && !launcher.getAttribute('data-disabled')) {
                launcher.style.display = 'block';
            }
            return;
        }

        // Setup event listeners
        setupEventListeners();

        // Check for existing container
        checkContainer();
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Launch buttons
        document.querySelectorAll('.launch-btn').forEach(btn => {
            btn.addEventListener('click', handleLaunch);
        });

        // Container control buttons
        const renewBtn = document.getElementById('renew-btn');
        if (renewBtn) {
            renewBtn.addEventListener('click', handleRenew);
        }

        const destroyBtn = document.getElementById('destroy-btn');
        if (destroyBtn) {
            destroyBtn.addEventListener('click', handleDestroy);
        }

        // Tab switching
        document.querySelectorAll('a[data-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', handleTabChange);
        });
    }

    /**
     * Handle launching a container
     * @param {Event} event - Click event
     */
    function handleLaunch(event) {
        const imageId = event.target.getAttribute('data-image-id');
        console.log('[WebShell] Launching container with image ID', imageId);
        console.log('[WebShell] API endpoint', config.apiEndpoint);
        console.log('[WebShell] Using CSRF token', config.csrfToken);

        // If not authenticated, redirect to login
        if (!config.isAuthed) {
            window.location.href = config.loginUrl;
            return;
        }

        // Add spinner to button
        const btn = event.target;
        const originalText = btn.textContent;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Launching...';
        btn.disabled = true;
        
        // Show info message
        showInfo('Launching WebShell, please wait...');
        
        // Prepare headers with CSRF token
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
        
        // Add CSRF token in multiple formats to ensure compatibility
        if (config.csrfToken) {
            headers['CSRF-Token'] = config.csrfToken;
            headers['X-CSRF-Token'] = config.csrfToken;
        }

        console.log('[WebShell] Sending POST request to', config.apiEndpoint);
        
        // Use fetch with credentials included to ensure cookies are sent
        fetch(config.apiEndpoint, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ image_id: imageId }),
            credentials: 'same-origin'  // This ensures cookies are sent with the request
        })
        .then(response => {
            console.log('[WebShell] Response status:', response.status);
            // Check if response is OK
            if (!response.ok) {
                // Try to get error details
                return response.text().then(text => {
                    console.error('[WebShell] Error response:', text);
                    try {
                        // Try to parse as JSON
                        const errorJson = JSON.parse(text);
                        throw new Error(errorJson.message || `Server error: ${response.status} ${response.statusText}`);
                    } catch (parseError) {
                        // If not JSON, use text
                        throw new Error(`Server error: ${response.status} ${response.statusText}`);
                    }
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('[WebShell] Response data:', data);
            if (data.success) {
                hideInfo();
                showInfo('Container created successfully!', 3000);
                // Wait a bit before checking container to allow for Docker setup
                setTimeout(checkContainer, 2000);
            } else {
                showError(data.message || 'Failed to launch WebShell');
                // Reset button state
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            console.error('[WebShell] Error launching WebShell:', error);
            showError('Failed to launch WebShell: ' + error.message);
            // Reset button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }

    /**
     * Handle renewing a container
     */
    function handleRenew() {
        showInfo('Renewing WebShell, please wait...');

        // Add spinner to button
        const btn = document.getElementById('renew-btn');
        const originalText = btn.textContent;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Renewing...';
        btn.disabled = true;

        // Prepare headers with CSRF token
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
        
        // Add CSRF token in multiple formats to ensure compatibility
        if (config.csrfToken) {
            headers['CSRF-Token'] = config.csrfToken;
            headers['X-CSRF-Token'] = config.csrfToken;
        }

        fetch(config.apiEndpoint, {
            method: 'PATCH',
            headers: headers,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showInfo('WebShell renewed successfully', 3000);
                checkContainer(); // Refresh container data
            } else {
                showError(data.message || 'Failed to renew WebShell');
            }
            
            // Reset button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        })
        .catch(error => {
            console.error('[WebShell] Error renewing WebShell:', error);
            showError('Failed to renew WebShell: ' + error.message);
            
            // Reset button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }

    /**
     * Handle destroying a container
     */
    function handleDestroy() {
        if (!confirm('Are you sure you want to destroy this WebShell? All data will be lost.')) {
            return;
        }

        showInfo('Destroying WebShell, please wait...');

        // Add spinner to button
        const btn = document.getElementById('destroy-btn');
        const originalText = btn.textContent;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Destroying...';
        btn.disabled = true;

        // Prepare headers with CSRF token
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
        
        // Add CSRF token in multiple formats to ensure compatibility
        if (config.csrfToken) {
            headers['CSRF-Token'] = config.csrfToken;
            headers['X-CSRF-Token'] = config.csrfToken;
        }

        fetch(config.apiEndpoint, {
            method: 'DELETE',
            headers: headers,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showInfo('WebShell destroyed successfully', 3000);
                
                // Clear intervals
                clearInterval(state.refreshInterval);
                clearInterval(state.timeRemainingInterval);
                
                // Reset state
                state.container = null;
                
                // Show launcher
                const launcher = document.getElementById('webshell-launcher');
                const container = document.getElementById('webshell-container');
                
                if (launcher) launcher.style.display = 'block';
                if (container) container.style.display = 'none';
            } else {
                showError(data.message || 'Failed to destroy WebShell');
                
                // Reset button state
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch(error => {
            console.error('[WebShell] Error destroying WebShell:', error);
            showError('Failed to destroy WebShell: ' + error.message);
            
            // Reset button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }

    /**
     * Handle tab change
     * @param {Event} event - Tab shown event
     */
    function handleTabChange(event) {
        try {
            const tabId = event.target.getAttribute('href');
            
            if (tabId === '#desktop-content' && state.container && state.container.has_desktop) {
                setupDesktopAccess();
            }
        } catch (error) {
            console.error('[WebShell] Error in tab change handler:', error);
        }
    }

    /**
     * Check for existing container
     */
    function checkContainer() {
        console.log('[WebShell] Checking for container...');
        
        // Prepare headers with CSRF token
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
        
        // Add CSRF token in multiple formats to ensure compatibility
        if (config.csrfToken) {
            headers['CSRF-Token'] = config.csrfToken;
            headers['X-CSRF-Token'] = config.csrfToken;
        }
        
        fetch(config.apiEndpoint, {
            method: 'GET',
            headers: headers,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // First hide any error message that might be showing
            hideError();
            
            console.log('[WebShell] Container data:', data);
            
            if (data.success) {
                if (data.data) {
                    // We have an active container
                    state.container = data.data;
                    setupContainerUI();
                } else {
                    // No active container, show launcher
                    const launcher = document.getElementById('webshell-launcher');
                    const container = document.getElementById('webshell-container');
                    
                    if (launcher) launcher.style.display = 'block';
                    if (container) container.style.display = 'none';
                }
            } else {
                // Handle API error
                console.error('[WebShell] API error:', data.message);
                showError(data.message || 'Failed to check WebShell status');
                
                // Still show container if we have it in state
                if (state.container) {
                    setupContainerUI();
                } else {
                    const launcher = document.getElementById('webshell-launcher');
                    const container = document.getElementById('webshell-container');
                    
                    if (launcher) launcher.style.display = 'block';
                    if (container) container.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('[WebShell] Error checking container:', error);
            showError('Failed to check WebShell status: ' + error.message);
            
            // Still show container if we have it in state
            if (state.container) {
                setupContainerUI();
            } else {
                const launcher = document.getElementById('webshell-launcher');
                const container = document.getElementById('webshell-container');
                
                if (launcher) launcher.style.display = 'block';
                if (container) container.style.display = 'none';
            }
        });
    }

    /**
     * Setup the container UI
     */
    function setupContainerUI() {
        // Hide launcher, show container
        const launcher = document.getElementById('webshell-launcher');
        const container = document.getElementById('webshell-container');
        
        if (launcher) launcher.style.display = 'none';
        if (container) container.style.display = 'block';
        
        try {
            // Set container title
            const titleElement = document.getElementById('desktop-title');
            if (titleElement && state.container) {
                titleElement.textContent = `Web Desktop - ${state.container.image_name || 'Container'}`;
            }
            
            // Update info tab
            updateInfoTab();
            
            // Setup desktop links
            setupDesktopAccess();
            
            // Setup countdown timer
            setupTimeRemaining();
            
            // Set refresh interval to periodically check container status
            if (state.refreshInterval) {
                clearInterval(state.refreshInterval);
            }
            state.refreshInterval = setInterval(checkContainer, 30000); // Check every 30 seconds
        } catch (error) {
            console.error('[WebShell] Error setting up container UI:', error);
            showError('Error setting up container UI: ' + error.message);
        }
    }

    /**
     * Setup desktop access
     */
    function setupDesktopAccess() {
        if (!state.container) return;
        
        // Update the direct link with the proper URL
        const directLink = document.getElementById('desktop-direct-link');
        if (directLink) {
            // Just use the container's desktop_url property which has the formatted HTML
            if (state.container.desktop_url) {
                try {
                    const userAccessDiv = document.createElement('div');
                    userAccessDiv.innerHTML = state.container.desktop_url;
                    
                    // Check if container section already exists and replace it
                    const existingAccess = document.getElementById('desktop-access-section');
                    if (existingAccess) {
                        existingAccess.innerHTML = '';
                        existingAccess.appendChild(userAccessDiv);
                    } else {
                        // Create a container for the user access HTML
                        const accessContainer = document.createElement('div');
                        accessContainer.id = 'desktop-access-section';
                        accessContainer.className = 'mt-3';
                        accessContainer.appendChild(userAccessDiv);
                        
                        // Replace the content of the desktop tab
                        const desktopContentDiv = document.getElementById('desktop-content');
                        if (desktopContentDiv) {
                            desktopContentDiv.innerHTML = '';
                            desktopContentDiv.appendChild(accessContainer);
                        }
                    }
                } catch (err) {
                    console.error('[WebShell] Error rendering desktop URL:', err);
                    // Fallback to a simple link if there's an error
                    const fallbackHTML = `
                        <div class="text-center py-3">
                            <a href="https://localhost:${state.container.desktop_port}" class="btn btn-primary" target="_blank">
                                Open Desktop (Port ${state.container.desktop_port})
                            </a>
                            <p class="mt-2"><small>Password: ${state.container.password || 'password'}</small></p>
                        </div>
                    `;
                    
                    const desktopContentDiv = document.getElementById('desktop-content');
                    if (desktopContentDiv) {
                        desktopContentDiv.innerHTML = fallbackHTML;
                    }
                }
            } else {
                // Fallback if no desktop_url is provided
                const fallbackHTML = `
                    <div class="text-center py-3">
                        <a href="https://localhost:${state.container.desktop_port}" class="btn btn-primary" target="_blank">
                            Open Desktop (Port ${state.container.desktop_port})
                        </a>
                        <p class="mt-2"><small>Password: ${state.container.password || 'password'}</small></p>
                    </div>
                `;
                
                const desktopContentDiv = document.getElementById('desktop-content');
                if (desktopContentDiv) {
                    desktopContentDiv.innerHTML = fallbackHTML;
                }
            }
        }
    }

    /**
     * Update info tab with container details
     */
    function updateInfoTab() {
        if (!state.container) return;
        
        // Helper function to safely update element text
        const updateElementText = (id, text) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = text;
            }
        };
        
        try {
            // Connection information
            updateElementText('info-desktop-url', state.container.desktop_url || '-');
            updateElementText('info-desktop-port', state.container.desktop_port || '-');
            updateElementText('info-password', state.container.password || '-');
            
            // Session information
            try {
                const startTime = new Date(state.container.start_time);
                updateElementText('info-start-time', startTime.toLocaleString());
            } catch (e) {
                updateElementText('info-start-time', '-');
            }
            
            updateElementText('info-time-remaining', formatTimeRemaining(state.container.remaining_time || 0));
            updateElementText('info-renewals', state.container.renew_count || 0);
            updateElementText('info-max-renewals', state.container.max_renew_count || 5);
            updateElementText('info-image', state.container.image_name || '-');
        } catch (error) {
            console.error('[WebShell] Error updating info tab:', error);
        }
    }

    /**
     * Setup time remaining countdown
     */
    function setupTimeRemaining() {
        if (state.timeRemainingInterval) {
            clearInterval(state.timeRemainingInterval);
        }
        
        // Make sure we have a container
        if (!state.container) return;
        
        try {
            // If remaining_time is missing or invalid, set a default
            if (typeof state.container.remaining_time !== 'number' || isNaN(state.container.remaining_time)) {
                // Get the timeout from the container's image timeout if available
                if (state.container.timeout && typeof state.container.timeout === 'number') {
                    state.container.remaining_time = state.container.timeout;
                } else {
                    // Default to 1 hour
                    state.container.remaining_time = 3600;
                }
            }
            
            // Update timer initially
            updateTimeRemaining();
            
            // Update every second
            state.timeRemainingInterval = setInterval(updateTimeRemaining, 1000);
        } catch (error) {
            console.error('[WebShell] Error setting up time remaining:', error);
        }
    }

    /**
     * Update time remaining display
     */
    function updateTimeRemaining() {
        try {
            if (!state.container) return;
            
            // Make sure remaining_time is a number
            if (typeof state.container.remaining_time !== 'number') {
                state.container.remaining_time = parseInt(state.container.remaining_time) || 3600; // Default to 1 hour if parsing fails
            }
            
            // Calculate remaining time (decrement by 1 second)
            state.container.remaining_time = Math.max(0, state.container.remaining_time - 1);
            
            // Update display
            const timeElement = document.getElementById('webshell-time-remaining');
            if (timeElement) {
                timeElement.textContent = formatTimeRemaining(state.container.remaining_time);
                
                // Change color based on time remaining
                if (state.container.remaining_time <= 300) { // 5 minutes
                    timeElement.classList.remove('badge-info', 'badge-warning');
                    timeElement.classList.add('badge-danger');
                } else if (state.container.remaining_time <= 600) { // 10 minutes
                    timeElement.classList.remove('badge-info', 'badge-danger');
                    timeElement.classList.add('badge-warning');
                } else {
                    timeElement.classList.remove('badge-danger', 'badge-warning');
                    timeElement.classList.add('badge-info');
                }
            }
            
            // Update info tab if it's visible
            const infoTimeElement = document.getElementById('info-time-remaining');
            if (infoTimeElement) {
                infoTimeElement.textContent = formatTimeRemaining(state.container.remaining_time);
            }
            
            // Check if time expired
            if (state.container.remaining_time <= 0) {
                clearInterval(state.timeRemainingInterval);
                showError('Your desktop environment has expired. Please renew or create a new one.');
                
                // Check container status after a short delay
                setTimeout(checkContainer, 2000);
            }
        } catch (error) {
            console.error('[WebShell] Error updating time remaining:', error);
        }
    }

    /**
     * Format time remaining as HH:MM:SS
     * @param {number} seconds - Time in seconds
     * @returns {string} Formatted time
     */
    function formatTimeRemaining(seconds) {
        try {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            return [
                hours.toString().padStart(2, '0'),
                minutes.toString().padStart(2, '0'),
                secs.toString().padStart(2, '0')
            ].join(':');
        } catch (error) {
            console.error('[WebShell] Error formatting time:', error);
            return '00:00:00';
        }
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    function showError(message) {
        try {
            const errorElement = document.getElementById('webshell-error');
            const errorMsgElement = document.getElementById('webshell-error-msg');
            
            if (errorElement && errorMsgElement) {
                errorMsgElement.textContent = message;
                errorElement.style.display = 'block';
                
                // Hide info message if showing
                hideInfo();
            }
        } catch (error) {
            console.error('[WebShell] Error showing error message:', error);
        }
    }

    /**
     * Hide error message
     */
    function hideError() {
        try {
            const errorElement = document.getElementById('webshell-error');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
        } catch (error) {
            console.error('[WebShell] Error hiding error message:', error);
        }
    }

    /**
     * Show info message
     * @param {string} message - Info message
     * @param {number} [timeout] - Auto-hide timeout in ms
     */
    function showInfo(message, timeout = 0) {
        try {
            const infoElement = document.getElementById('webshell-info');
            const infoMsgElement = document.getElementById('webshell-info-msg');
            
            if (infoElement && infoMsgElement) {
                infoMsgElement.textContent = message;
                infoElement.style.display = 'block';
                
                // Hide error message if showing
                hideError();
                
                // Auto-hide after timeout if specified
                if (timeout > 0) {
                    setTimeout(hideInfo, timeout);
                }
            }
        } catch (error) {
            console.error('[WebShell] Error showing info message:', error);
        }
    }

    /**
     * Hide info message
     */
    function hideInfo() {
        try {
            const infoElement = document.getElementById('webshell-info');
            if (infoElement) {
                infoElement.style.display = 'none';
            }
        } catch (error) {
            console.error('[WebShell] Error hiding info message:', error);
        }
    }

    // Public API
    return {
        init: init
    };
})();
