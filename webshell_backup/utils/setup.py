from CTFd.utils import set_config
from flask import current_app

from ..models import WebShellImage, db

def setup_default_configs():
    """
    Set up default configurations for the WebShell plugin
    """
    current_app.logger.info("[WebShell] Setting up default configurations")
    
    # Create default configurations - match whale's approach
    for key, val in {
        'setup': 'true',
        'domain': 'localhost',
        'max_container_count': '100',
        'max_renew_count': '5',
        'container_timeout': '3600',
        'https_required': 'true',  # Kasm requires HTTPS
    }.items():
        set_config('webshell:' + key, val)
        current_app.logger.info(f"[WebShell] Set config {key} = {val}")
    
    # Create default image if none exists
    if WebShellImage.query.count() == 0:
        current_app.logger.info("[WebShell] Creating default Kasm image")
        
        # Create a default Kasm image
        default_image = WebShellImage(
            name="Kali Linux Desktop",
            description="Kali Linux with web-based desktop access via Kasm",
            docker_image="kasmweb/kali-rolling-desktop:1.14.0",
            memory_limit="1024m",
            cpu_limit=1.0,
            timeout=3600,
            port=6901,  # Kasm default port
            has_desktop=True,
            desktop_port=6901,  # Same as port for Kasm
            active=True
        )
        
        db.session.add(default_image)
        
        try:
            db.session.commit()
            current_app.logger.info("[WebShell] Default Kasm image created successfully")
        except Exception as e:
            current_app.logger.error(f"[WebShell] Error creating default image: {str(e)}")
            db.session.rollback()
    
    current_app.logger.info("[WebShell] Default configuration setup complete")
