// Ultra-simple loading animation with guaranteed form submission and timeout
(function() {
    console.log('Enhanced simple loading script loaded');

    // Wait for DOM to be ready
    function initialize() {
        console.log('Initializing enhanced simple loading script');

        // Find all launch buttons
        const launchButtons = document.querySelectorAll('.launch-btn');
        console.log('Found ' + launchButtons.length + ' launch buttons');

        // Add click handler to each button
        launchButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                console.log('Button clicked');

                // Find the form that contains this button
                const form = this.closest('form');
                if (!form) {
                    console.error('No form found');
                    return;
                }

                // Change button text to show it's working
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Launching...';
                this.disabled = true;

                // Create a simple loading overlay
                const overlay = document.createElement('div');
                overlay.id = 'enhanced-loading-overlay';
                overlay.style.position = 'fixed';
                overlay.style.top = '0';
                overlay.style.left = '0';
                overlay.style.width = '100%';
                overlay.style.height = '100%';
                overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
                overlay.style.zIndex = '99999';
                overlay.style.display = 'flex';
                overlay.style.flexDirection = 'column';
                overlay.style.justifyContent = 'center';
                overlay.style.alignItems = 'center';
                document.body.appendChild(overlay);

                // Create loading spinner
                const spinner = document.createElement('div');
                spinner.style.width = '80px';
                spinner.style.height = '80px';
                spinner.style.border = '6px solid #444';
                spinner.style.borderTop = '6px solid #007bff';
                spinner.style.borderRadius = '50%';
                spinner.style.marginBottom = '20px';

                // Add animation
                spinner.style.animation = 'spin 1s linear infinite';
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `;
                document.head.appendChild(style);
                overlay.appendChild(spinner);

                // Add text
                const text = document.createElement('div');
                text.id = 'loading-message';
                text.style.color = 'white';
                text.style.fontSize = '22px';
                text.style.textAlign = 'center';
                text.style.marginBottom = '15px';
                text.innerHTML = 'Preparing your desktop environment...<br>Please wait a moment.';
                overlay.appendChild(text);

                // Add status text
                const statusText = document.createElement('div');
                statusText.id = 'loading-status';
                statusText.style.color = '#6fc2ff';
                statusText.style.fontSize = '18px';
                statusText.style.textAlign = 'center';
                statusText.style.marginBottom = '15px';
                statusText.innerHTML = 'Initializing...';
                overlay.appendChild(statusText);

                // Add progress bar
                const progressContainer = document.createElement('div');
                progressContainer.style.width = '300px';
                progressContainer.style.height = '10px';
                progressContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                progressContainer.style.borderRadius = '5px';
                progressContainer.style.overflow = 'hidden';
                progressContainer.style.marginBottom = '20px';

                const progressBar = document.createElement('div');
                progressBar.id = 'loading-progress';
                progressBar.style.width = '0%';
                progressBar.style.height = '100%';
                progressBar.style.backgroundColor = '#007bff';
                progressBar.style.borderRadius = '5px';
                progressBar.style.transition = 'width 0.5s';

                progressContainer.appendChild(progressBar);
                overlay.appendChild(progressContainer);

                // Add retry button (hidden initially)
                const retryButton = document.createElement('button');
                retryButton.id = 'retry-button';
                retryButton.style.display = 'none';
                retryButton.style.padding = '10px 20px';
                retryButton.style.backgroundColor = '#007bff';
                retryButton.style.color = 'white';
                retryButton.style.border = 'none';
                retryButton.style.borderRadius = '5px';
                retryButton.style.cursor = 'pointer';
                retryButton.style.marginTop = '20px';
                retryButton.innerHTML = 'Retry';
                retryButton.onclick = function() {
                    // Hide error message and retry button
                    statusText.innerHTML = 'Retrying...';
                    statusText.style.color = '#6fc2ff';
                    retryButton.style.display = 'none';

                    // Reset progress bar
                    progressBar.style.width = '0%';

                    // Try to submit the form again
                    submitForm();
                };
                overlay.appendChild(retryButton);

                // Add error message container (hidden initially)
                const errorMessage = document.createElement('div');
                errorMessage.id = 'error-message';
                errorMessage.style.display = 'none';
                errorMessage.style.color = '#ff6b6b';
                errorMessage.style.fontSize = '16px';
                errorMessage.style.textAlign = 'center';
                errorMessage.style.marginTop = '10px';
                errorMessage.style.maxWidth = '80%';
                overlay.appendChild(errorMessage);

                // Status messages
                const messages = [
                    'Initializing...',
                    'Creating container...',
                    'Allocating resources...',
                    'Setting up environment...',
                    'Configuring network...',
                    'Starting desktop services...',
                    'Preparing user interface...',
                    'Almost ready...',
                    'Finalizing setup...'
                ];

                // Update status and progress
                let messageIndex = 0;
                const statusInterval = setInterval(() => {
                    messageIndex = (messageIndex + 1) % messages.length;
                    statusText.innerHTML = messages[messageIndex];

                    // Update progress bar
                    const currentWidth = parseInt(progressBar.style.width) || 0;
                    if (currentWidth < 90) { // Cap at 90% until we know it's successful
                        progressBar.style.width = (currentWidth + 10) + '%';
                    }
                }, 3000);

                // Function to submit the form
                function submitForm() {
                    try {
                        console.log('Submitting the form now');

                        // Create a new form for submission
                        const newForm = document.createElement('form');
                        newForm.method = form.method;
                        newForm.action = form.action;

                        // Copy all input fields
                        const inputs = form.querySelectorAll('input');
                        inputs.forEach(input => {
                            const newInput = document.createElement('input');
                            newInput.type = input.type;
                            newInput.name = input.name;
                            newInput.value = input.value;
                            newForm.appendChild(newInput);
                        });

                        // Add form to document
                        document.body.appendChild(newForm);

                        // Submit the form
                        newForm.submit();

                    } catch(error) {
                        console.error('Error submitting form:', error);

                        // Fallback - try to submit the original form
                        try {
                            // Remove all event listeners by cloning the form
                            const clone = form.cloneNode(true);
                            form.parentNode.replaceChild(clone, form);

                            // Submit the cloned form
                            setTimeout(function() {
                                clone.submit();
                            }, 100);

                        } catch(innerError) {
                            console.error('Fallback submission failed:', innerError);

                            // Show error and retry button
                            showError('Error launching desktop. Please try again.');
                        }
                    }
                }

                // Function to show error
                function showError(message) {
                    // Clear status update interval
                    clearInterval(statusInterval);

                    // Update status text
                    statusText.innerHTML = 'Error';
                    statusText.style.color = '#ff6b6b';

                    // Show error message
                    errorMessage.innerHTML = message;
                    errorMessage.style.display = 'block';

                    // Show retry button
                    retryButton.style.display = 'block';

                    // Add a reload button
                    const reloadButton = document.createElement('button');
                    reloadButton.style.padding = '10px 20px';
                    reloadButton.style.backgroundColor = '#6c757d';
                    reloadButton.style.color = 'white';
                    reloadButton.style.border = 'none';
                    reloadButton.style.borderRadius = '5px';
                    reloadButton.style.cursor = 'pointer';
                    reloadButton.style.marginTop = '20px';
                    reloadButton.style.marginLeft = '10px';
                    reloadButton.innerHTML = 'Reload Page';
                    reloadButton.onclick = function() {
                        window.location.reload();
                    };
                    retryButton.parentNode.insertBefore(reloadButton, retryButton.nextSibling);
                }

                // Set a timeout to detect if we're stuck
                const timeout = setTimeout(() => {
                    // Check if we're still on the same page
                    if (document.getElementById('enhanced-loading-overlay')) {
                        showError('The desktop is taking longer than expected to launch. This could be due to server load or network issues.');
                    }
                }, 45000); // 45 second timeout

                // Schedule the form submission
                setTimeout(submitForm, 5000); // 5 second delay before submission

                // Prevent the default form submission
                event.preventDefault();
                return false;
            });
        });
    }

    // Run on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Make sure loading overlay is hidden
            const existingOverlay = document.getElementById('loading-overlay');
            if (existingOverlay) {
                existingOverlay.style.display = 'none';
                console.log('Hiding existing loading overlay');
            }

            // Initialize the loader
            initialize();
        });
    } else {
        // DOM is already ready
        // Make sure loading overlay is hidden
        const existingOverlay = document.getElementById('loading-overlay');
        if (existingOverlay) {
            existingOverlay.style.display = 'none';
            console.log('Hiding existing loading overlay (DOM ready)');
        }

        // Initialize the loader
        initialize();
    }
})();
