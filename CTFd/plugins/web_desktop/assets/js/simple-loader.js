// Ultra-simple loading animation with guaranteed form submission
(function() {
    console.log('Simple loading script loaded');
    
    // Wait for DOM to be ready
    function initialize() {
        console.log('Initializing simple loading script');
        
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
                text.style.color = 'white';
                text.style.fontSize = '22px';
                text.style.textAlign = 'center';
                text.style.marginBottom = '15px';
                text.innerHTML = 'Preparing your desktop environment...<br>Please wait a moment.';
                overlay.appendChild(text);
                
                // Schedule the form submission
                setTimeout(function() {
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
                            
                            // Last resort - redirect to the form's action URL
                            window.location.href = form.action;
                        }
                    }
                }, 5000); // 5 second delay before submission
                
                // Prevent the default form submission
                event.preventDefault();
                return false;
            });
        });
    }
    
    // Run on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // DOM is already ready
        initialize();
    }
})();
