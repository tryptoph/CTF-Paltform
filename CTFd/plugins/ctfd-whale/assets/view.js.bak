CTFd._internal.challenge.data = undefined

CTFd._internal.challenge.renderer = CTFd.lib.markdown();

CTFd._internal.challenge.preRender = function () {
}

CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown)
}

CTFd._internal.challenge.postRender = function () {
    loadInfo();
}

if ($ === undefined) $ = CTFd.lib.$;

// Function to open the challenge in a new window
function openChallengeWindow() {
    // Get the port from the global variable
    const port = window.challengePort;
    if (port) {
        // Create URL with appropriate protocol
        const url = 'http://localhost:' + port;
        console.log('Opening challenge at:', url);
        // Open in a new window - this bypasses some browser restrictions
        window.open(url, '_blank');
    } else {
        // Try to get the port again by refreshing the info
        loadInfo(true);
    }
}

// Helper function to format seconds to HH:MM:SS
function formatTimeHMS(seconds) {
    if (seconds < 0) seconds = 0;
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    // Format with leading zeros
    let timeString = '';
    
    if (hours > 0) {
        timeString += hours + 'h ';
    }
    
    if (hours > 0 || minutes > 0) {
        timeString += minutes + 'm ';
    }
    
    timeString += remainingSeconds + 's';
    
    return timeString;
}

// Track if the container is loaded already
// We'll also store this in sessionStorage to persist across refreshes
let containerLoaded = sessionStorage.getItem('containerLoaded') === 'true';

function loadInfo(forceRefresh = false) {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    var params = {};

    CTFd.fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (window.t !== undefined) {
            clearInterval(window.t);
            window.t = undefined;
        }
        if (response.success) response = response.data;
        else CTFd.ui.ezq.ezAlert({
            title: "Fail",
            body: response.message,
            button: "OK"
        });
        if (response.remaining_time === undefined) {
            $('#whale-panel').html('<div class="card" style="width: 100%;">' +
                '<div class="card-body" style="text-align: center;">' +
                '<h5 class="card-title">Instance Info</h5>' +
                '<button type="button" class="btn btn-primary" id="whale-button-boot" ' +
                'style="background-color: #007bff; color: white; padding: 12px 25px; ' +
                'border: none; cursor: pointer; border-radius: 4px; display: inline-block; ' +
                'margin: 10px 0; font-weight: bold; font-size: 16px; letter-spacing: 0.5px; ' +
                'box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: all 0.3s ease;" ' +
                'onmouseover="this.style.backgroundColor=\'#0069d9\'; this.style.transform=\'translateY(-3px)\'; ' +
                'this.style.boxShadow=\'0 6px 10px rgba(0,0,0,0.3)\';" ' +
                'onmouseout="this.style.backgroundColor=\'#007bff\'; this.style.transform=\'translateY(0)\'; ' +
                'this.style.boxShadow=\'0 4px 6px rgba(0,0,0,0.2)\';" ' +
                'onclick="CTFd._internal.challenge.boot()">' +
                '<i class="fas fa-rocket"></i> Launch an instance</button>' +
                '</div>' +
                '</div>');
        } else {
            // Format the time using the new function
            const formattedTime = formatTimeHMS(response.remaining_time);
            
            // Store port for the open challenge button
            window.challengePort = response.port;
            console.log('Port set to:', window.challengePort);
            
            // If responding to a direct API call for an existing container,
            // assume container is already loaded
            if (response.port) {
                containerLoaded = true;
                sessionStorage.setItem('containerLoaded', 'true');
            }
            
            // Check if this is the first time loading the container or if we need to force a refresh
            const shouldShowSpinner = !containerLoaded || forceRefresh;
            
            // Create the HTML structure for the panel
            let panelHtml = 
                '<div class="card" style="width: 100%;">' +
                '<div class="card-body">' +
                '<h5 class="card-title">Instance Info</h5>' +
                '<h6 class="card-subtitle mb-2 text-muted" id="whale-challenge-count-down" data-seconds="' + response.remaining_time + '">Remaining Time: ' + formattedTime + '</h6>' +
                '<h6 class="card-subtitle mb-2 text-muted">Lan Domain: ' + response.lan_domain + '</h6>' +
                '<div id="challenge-access-container" style="margin: 15px 0;">';
                
            // Show different content based on whether we should show the spinner
            if (shouldShowSpinner) {
                // For new containers, show the loading spinner
                panelHtml += '<div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">' +
                           '<span class="sr-only">Loading...</span>' +
                           '</div>';
            } else {
                // For existing containers, show the open button immediately
                panelHtml += '<button onclick="openChallengeWindow()" ' +
                           'class="btn btn-primary" ' +
                           'style="background-color: #007bff; color: white; padding: 12px 25px; ' +
                           'border: none; cursor: pointer; border-radius: 4px; display: inline-block; ' +
                           'margin: 10px 0; font-weight: bold; font-size: 16px; letter-spacing: 0.5px; ' +
                           'box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: all 0.3s ease;" ' +
                           'onmouseover="this.style.backgroundColor=\'#0069d9\'; this.style.transform=\'translateY(-3px)\'; ' +
                           'this.style.boxShadow=\'0 6px 10px rgba(0,0,0,0.3)\';" ' +
                           'onmouseout="this.style.backgroundColor=\'#007bff\'; this.style.transform=\'translateY(0)\'; ' +
                           'this.style.boxShadow=\'0 4px 6px rgba(0,0,0,0.2)\';">' +
                           '<i class="fas fa-external-link-alt"></i> Open Challenge</button>';
            }
            
            // Complete the HTML
            panelHtml += '</div>' +
                       '<button type="button" class="btn btn-danger card-link" id="whale-button-destroy" onclick="CTFd._internal.challenge.destroy()">Destroy this instance</button>' +
                       '<button type="button" class="btn btn-success card-link" id="whale-button-renew" onclick="CTFd._internal.challenge.renew()">Renew this instance</button>' +
                       '</div>' +
                       '</div>';
            
            // Update the panel with our HTML
            $('#whale-panel').html(panelHtml);

            function showAuto() {
                const countdownElement = $('#whale-challenge-count-down')[0];
                if (countdownElement === undefined) return;
                
                // Get the seconds from the data attribute
                let seconds = parseInt(countdownElement.getAttribute('data-seconds')) - 1;
                countdownElement.setAttribute('data-seconds', seconds);
                
                // Format the time for display
                const formattedTime = formatTimeHMS(seconds);
                countdownElement.innerHTML = 'Remaining Time: ' + formattedTime;
                
                if (seconds < 0) {
                    loadInfo();
                }
            }

            // Only start the timer after the spinner is done if showing spinner
            if (!shouldShowSpinner) {
                // Start the timer immediately for existing containers
                window.t = setInterval(showAuto, 1000);
            }
            
            // After 3 seconds, replace the spinner with the Open Challenge button, but only if showing spinner
            if (shouldShowSpinner) {
                setTimeout(function() {
                    $('#challenge-access-container').html(
                        '<button onclick="openChallengeWindow()" ' +
                        'class="btn btn-primary" ' +
                        'style="background-color: #007bff; color: white; padding: 12px 25px; ' +
                        'border: none; cursor: pointer; border-radius: 4px; display: inline-block; ' +
                        'margin: 10px 0; font-weight: bold; font-size: 16px; letter-spacing: 0.5px; ' +
                        'box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: all 0.3s ease;" ' +
                        'onmouseover="this.style.backgroundColor=\'#0069d9\'; this.style.transform=\'translateY(-3px)\'; ' +
                        'this.style.boxShadow=\'0 6px 10px rgba(0,0,0,0.3)\';" ' +
                        'onmouseout="this.style.backgroundColor=\'#007bff\'; this.style.transform=\'translateY(0)\'; ' +
                        'this.style.boxShadow=\'0 4px 6px rgba(0,0,0,0.2)\';">' +
                        '<i class="fas fa-external-link-alt"></i> Open Challenge</button>'
                    );
                    
                    // Mark that container is now loaded
                    containerLoaded = true;
                    sessionStorage.setItem('containerLoaded', 'true');
                    
                    // Now start the timer for this container
                    window.t = setInterval(showAuto, 1000);
                }, 3000);
            }
        }
    });
};

CTFd._internal.challenge.destroy = function () {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    $('#whale-button-destroy')[0].innerHTML = "Waiting...";
    $('#whale-button-destroy')[0].disabled = true;

    var params = {};

    CTFd.fetch(url, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            // Reset container loaded state when a container is destroyed
            containerLoaded = false;
            sessionStorage.setItem('containerLoaded', 'false');
            
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: "Success",
                body: "Your instance has been destroyed!",
                button: "OK"
            });
        } else {
            $('#whale-button-destroy')[0].innerHTML = "Destroy this instance";
            $('#whale-button-destroy')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: "Fail",
                body: response.message,
                button: "OK"
            });
        }
    });
};

CTFd._internal.challenge.renew = function () {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    $('#whale-button-renew')[0].innerHTML = "Waiting...";
    $('#whale-button-renew')[0].disabled = true;

    var params = {};

    CTFd.fetch(url, {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: "Success",
                body: "Your instance has been renewed!",
                button: "OK"
            });
        } else {
            $('#whale-button-renew')[0].innerHTML = "Renew this instance";
            $('#whale-button-renew')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: "Fail",
                body: response.message,
                button: "OK"
            });
        }
    });
};

CTFd._internal.challenge.boot = function () {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    // Better loading indicator
    $('#whale-button-boot').html('<i class="fas fa-spinner fa-spin"></i> Starting...');
    $('#whale-button-boot').prop('disabled', true);

    var params = {};

    CTFd.fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            // Reset container loaded state when a new container is created
            containerLoaded = false;
            sessionStorage.setItem('containerLoaded', 'false');
            
            // Load the updated info (which will show the spinner)
            loadInfo(true);
            
            // Wait 3 seconds (same as spinner duration) then show success message
            setTimeout(function() {
                CTFd.ui.ezq.ezAlert({
                    title: "Success",
                    body: "Your instance has been deployed!",
                    button: "OK"
                });
            }, 3000);
        } else {
            $('#whale-button-boot').html('<i class="fas fa-rocket"></i> Launch an instance');
            $('#whale-button-boot').prop('disabled', false);
            CTFd.ui.ezq.ezAlert({
                title: "Fail",
                body: response.message,
                button: "OK"
            });
        }
    });
};


CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = $('#challenge-id').val();
    var submission = $('#challenge-input').val()

    var body = {
        'challenge_id': challenge_id,
        'submission': submission,
    }
    var params = {}
    if (preview)
        params['preview'] = true

    return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response
        }
        return response
    })
};