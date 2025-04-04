#!/bin/bash

# Set the base path to your CTFd theme
BASE_PATH="/mnt/c/Users/ilyas/Desktop/CTFd_with_CTFd-whale/CTFd/themes/CTFd-theme-pixo"

# Create JS fix file
JS_DIR="${BASE_PATH}/static/js"
JS_FILE="${JS_DIR}/fix-solved.js"
echo "Creating JavaScript fix at ${JS_FILE}"

# Make directory if it doesn't exist
mkdir -p "${JS_DIR}"

cat > "${JS_FILE}" << 'EOF'
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
EOF

# Create CSS fix file
CSS_DIR="${BASE_PATH}/static/css"
CSS_FILE="${CSS_DIR}/fix-solved.css"
echo "Creating CSS fix at ${CSS_FILE}"

# Make directory if it doesn't exist
mkdir -p "${CSS_DIR}"

cat > "${CSS_FILE}" << 'EOF'
.solved-challenge {
  background-color: #37d63e !important;
  opacity: 0.9 !important;
  border: 2px solid #ffd700 !important;
}

.corner-button-check {
  position: absolute !important;
  top: 5px !important;
  right: 5px !important;
  color: #ffd700 !important;
  font-size: 16px !important;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.7) !important;
}
EOF

# Update challenges.html
HTML_DIR="${BASE_PATH}/templates"
HTML_FILE="${HTML_DIR}/challenges.html"
echo "Modifying ${HTML_FILE}"

# Check if file exists
if [ ! -f "${HTML_FILE}" ]; then
  echo "Error: ${HTML_FILE} does not exist"
  exit 1
fi

# Backup the original file
cp "${HTML_FILE}" "${HTML_FILE}.bak"
echo "Created backup at ${HTML_FILE}.bak"

# Check for existing inclusions to avoid duplicates
if grep -q "fix-solved.js" "${HTML_FILE}"; then
  echo "Fix already included in HTML file. No changes made."
else
  # Add the fix script and CSS before the closing body tag
  sed -i 's/<\/body>/<!-- Fix for solved challenges -->\n<link rel="stylesheet" href="{{ url_for('\''views.themes'\'', path=theme.styles + '\''/fix-solved.css'\'') }}">\n<script src="{{ url_for('\''views.themes'\'', path=theme.scripts + '\''/fix-solved.js'\'') }}"><\/script>\n<\/body>/g' "${HTML_FILE}"
  echo "Successfully updated ${HTML_FILE}"
fi

echo "Setup complete. Please restart your CTFd server for the changes to take effect."