from CTFd.utils import set_config
from flask import current_app

from ..models import DesktopImage, db


def setup_default_configs():
    """
    Set up default configurations for the Web Desktop plugin
    """
    current_app.logger.info("[Web Desktop] Setting up default configurations")
    
    # Create default configurations
    for key, val in {
        'setup': 'true',
        'domain': 'localhost',
        'max_instances': '100',
        'max_renew_count': '5',
        'instance_timeout': '3600',
    }.items():
        set_config('desktop:' + key, val)
        current_app.logger.info(f"[Web Desktop] Set config {key} = {val}")
    
    # Create default image if none exists
    if DesktopImage.query.count() == 0:
        current_app.logger.info("[Web Desktop] Creating default Kasm image")
        
        # Create a default Kasm image
        default_image = DesktopImage(
            name="Kali Linux Desktop",
            description="Kali Linux with web-based desktop access via Kasm",
            docker_image="kasmweb/kali-rolling-desktop:1.14.0",
            memory_limit="1024m",
            cpu_limit=1.0,
            timeout=3600,
            desktop_port=6901,
            active=True
        )
        
        db.session.add(default_image)
        
        try:
            db.session.commit()
            current_app.logger.info("[Web Desktop] Default Kasm image created successfully")
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error creating default image: {str(e)}")
            db.session.rollback()
    
    current_app.logger.info("[Web Desktop] Default configuration setup complete")
