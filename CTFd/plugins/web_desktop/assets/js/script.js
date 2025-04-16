/**
 * Kali Web Desktop Plugin JavaScript
 */

// Handle desktop launching
function launchDesktop() {
    // Disable button and show loading
    $('#launch-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Starting Desktop...');

    // Call the API to launch a desktop
    fetch('/api/v1/plugins/webdesktop/kali', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showResponse('Desktop is starting. This page will refresh in a few seconds...', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } else {
            showResponse(data.message);
            $('#launch-btn').prop('disabled', false).html('<i class="fas fa-rocket"></i> Launch Kali Desktop');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showResponse('An unexpected error occurred');
        $('#launch-btn').prop('disabled', false).html('<i class="fas fa-rocket"></i> Launch Kali Desktop');
    });
}

// Show response message
function showResponse(message, type = 'danger') {
    $('#desktop-response').html(
        `<div class="alert alert-${type} alert-dismissable" role="alert">
            <span>${message}</span>
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">×</span>
            </button>
        </div>`
    );

    // Scroll to top to show message
    window.scrollTo(0, 0);
}

// Renew container
function renewContainer() {
    $('#renew-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Renewing...');

    fetch('/api/v1/plugins/ctfd-whale/container', {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            showResponse(data.message);
            $('#renew-btn').prop('disabled', false).html('<i class="fas fa-sync-alt"></i> Renew Session');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showResponse('An unexpected error occurred');
        $('#renew-btn').prop('disabled', false).html('<i class="fas fa-sync-alt"></i> Renew Session');
    });
}

// Delete container
function deleteContainer() {
    $('#delete-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Deleting...');

    fetch('/api/v1/plugins/ctfd-whale/container', {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            showResponse(data.message);
            $('#delete-btn').prop('disabled', false).html('<i class="fas fa-trash-alt"></i> Delete Session');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showResponse('An unexpected error occurred');
        $('#delete-btn').prop('disabled', false).html('<i class="fas fa-trash-alt"></i> Delete Session');
    });
}

// Admin: Delete a specific container
function adminDeleteContainer(userId) {
    if (confirm('Are you sure you want to delete this desktop instance?')) {
        fetch(`/api/v1/plugins/ctfd-whale-admin/container?user_id=${userId}`, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the container');
        });
    }
}

// Admin: Delete all containers
function adminDeleteAllContainers() {
    if (confirm('Are you sure you want to delete ALL desktop instances? This cannot be undone.')) {
        fetch('/api/v1/plugins/webdesktop-admin/containers', {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the containers');
        });
    }
}

// Initialize timer when container exists
function initializeTimer(startTimeIso, timeout) {
    // Calculate remaining time
    const startTime = new Date(startTimeIso);
    const currentTime = new Date();
    const elapsedSeconds = Math.floor((currentTime - startTime) / 1000);
    let remainingSeconds = Math.max(0, timeout - elapsedSeconds);

    // Format time function
    function formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else {
            return `${minutes}m ${secs}s`;
        }
    }

    // Update progress bar
    function updateProgressBar(seconds) {
        const percentage = Math.floor((seconds / timeout) * 100);
        $('#time-progress').css('width', `${percentage}%`).attr('aria-valuenow', percentage).text(`${percentage}%`);

        // Change color based on time remaining
        if (percentage < 20) {
            $('#time-progress').removeClass('bg-success bg-warning').addClass('bg-danger');
        } else if (percentage < 50) {
            $('#time-progress').removeClass('bg-success bg-danger').addClass('bg-warning');
        } else {
            $('#time-progress').removeClass('bg-warning bg-danger').addClass('bg-success');
        }

        // Mark as expiring soon if less than 5 minutes
        if (seconds < 300) {
            $('#remaining-time').addClass('expiring-soon');
        }
    }

    // Update the timer immediately
    if (document.getElementById('remaining-time')) {
        document.getElementById('remaining-time').textContent = formatTime(remainingSeconds);
        updateProgressBar(remainingSeconds);

        // Set a timer to update every second
        const timer = setInterval(() => {
            remainingSeconds--;

            if (remainingSeconds <= 0) {
                clearInterval(timer);
                document.getElementById('remaining-time').textContent = 'Expired';
                $('#time-progress').css('width', '0%').attr('aria-valuenow', 0).text('0%');
                $('#time-progress').removeClass('bg-success bg-warning').addClass('bg-danger');

                // Show message
                showResponse('Your desktop session has expired', 'warning');

                // Reload the page after a short delay to reflect the expired state
                setTimeout(() => window.location.reload(), 3000);
            } else {
                document.getElementById('remaining-time').textContent = formatTime(remainingSeconds);
                updateProgressBar(remainingSeconds);
            }
        }, 1000);
    }
}
