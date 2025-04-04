(function() {
  // Wait for the page to fully load
  window.addEventListener('load', function() {
    console.log("Applying solved challenges fix");
    
    // Replace the markSolves function
    window.markSolves = function() {
      // Make a direct API call to get user solves
      return fetch('/api/v1/users/me/solves')
        .then(response => response.json())
        .then(function(response) {
          if (response.success) {
            const solves = response.data;
            console.log("Found " + solves.length + " solved challenges");
            
            // Mark each solved challenge
            for (let i = 0; i < solves.length; i++) {
              const challengeId = solves[i].challenge_id;
              const btn = $('button[value="' + challengeId + '"]');
              
              if (btn.length > 0) {
                console.log("Marking challenge " + challengeId + " as solved");
                
                // Apply solved styling
                btn.addClass("solved-challenge");
                
                // Remove existing check icon to prevent duplicates
                btn.find('.fa-check.corner-button-check').remove();
                
                // Add check icon
                btn.prepend("<i class='fas fa-check corner-button-check'></i>");
              }
            }
          }
        });
    };
    
    // Call our new markSolves function after a short delay
    setTimeout(markSolves, 1000);
    
    // Set an interval to periodically refresh the solved status
    setInterval(markSolves, 10000);
  });
})();
