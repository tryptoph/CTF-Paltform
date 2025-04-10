#!/usr/bin/env python
"""
WebShell Plugin - Kasm Image Configuration Updater
This script updates existing WebShell image configurations to properly work with Kasm containers.
"""

import os
import sys

# Add CTFd to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))

# Import necessary modules
from CTFd import create_app
from CTFd.models import db
from CTFd.plugins.webshell.models import WebShellImage, WebShellConfig
from CTFd.utils import set_config

def update_kasm_config():
    """Update WebShell image configurations for Kasm compatibility"""
    print("Updating WebShell image configurations for Kasm compatibility...")
    
    # Get all WebShell images
    images = WebShellImage.query.all()
    
    for image in images:
        # Check if this appears to be a Kasm image
        if 'kasm' in image.docker_image.lower() or 'kasmweb' in image.docker_image.lower():
            print(f"Updating image: {image.name} ({image.docker_image})")
            
            # Update port to 6901 (Kasm web interface)
            image.port = 6901
            
            # If has_desktop is True, update desktop_port to match
            if image.has_desktop:
                image.desktop_port = 6901
            
            # Ensure sufficient memory for Kasm (minimum 512MB)
            mem_numeric = int(''.join(filter(str.isdigit, image.memory_limit)))
            mem_unit = ''.join(filter(str.isalpha, image.memory_limit))
            
            if mem_unit.lower() == 'm' and mem_numeric < 512:
                image.memory_limit = "512m"
                print(f"  Increased memory limit to {image.memory_limit}")
            
            # Update or add shared memory size configuration
            if image.has_desktop:
                # Increase timeout for desktop environments
                if image.timeout < 3600:
                    image.timeout = 3600
                    print(f"  Increased timeout to {image.timeout} seconds")
    
    # Update domain configuration if it's localhost
    domain_config = WebShellConfig.query.filter_by(key="domain").first()
    if domain_config and domain_config.value == "localhost":
        print("Ensuring domain configuration is properly set...")
        # This ensures we use the same domain in the URL as the browser is using
        # Alternatively, you could set this to a specific domain
        set_config("webshell:domain", "localhost")
    
    # Save changes
    db.session.commit()
    print("Done! WebShell configuration updated for Kasm compatibility.")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        update_kasm_config()
