import datetime
from CTFd.models import db, Users
from CTFd.utils import get_config

class WebShellConfig(db.Model):
    """
    WebShell configuration model for storing plugin settings
    """
    __tablename__ = 'webshell_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    
    def __init__(self, key, value):
        self.key = key
        self.value = value

class WebShellImage(db.Model):
    """
    WebShell image model for storing available container images
    """
    __tablename__ = 'webshell_images'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    docker_image = db.Column(db.String(80), nullable=False)
    memory_limit = db.Column(db.String(32), nullable=False, default='256m')
    cpu_limit = db.Column(db.Float, nullable=False, default=0.5)
    timeout = db.Column(db.Integer, nullable=False, default=3600)
    port = db.Column(db.Integer, nullable=False, default=22)
    has_desktop = db.Column(db.Boolean, nullable=False, default=False)
    desktop_port = db.Column(db.Integer, nullable=False, default=5900)
    active = db.Column(db.Boolean, nullable=False, default=True)
    
    def __init__(self, name, docker_image, description='', memory_limit='256m', cpu_limit=0.5,
                 timeout=3600, port=22, has_desktop=False, desktop_port=5900, active=True):
        self.name = name
        self.description = description
        self.docker_image = docker_image
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.timeout = timeout
        self.port = port
        self.has_desktop = has_desktop
        self.desktop_port = desktop_port
        self.active = active

class WebShellContainer(db.Model):
    """
    WebShell container model for tracking active containers
    """
    __tablename__ = 'webshell_containers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    image_id = db.Column(db.Integer, db.ForeignKey('webshell_images.id'), nullable=False)
    uuid = db.Column(db.String(36), nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)  # 0: creating, 1: running, 2: error
    shell_port = db.Column(db.Integer, nullable=True)
    desktop_port = db.Column(db.Integer, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    renew_count = db.Column(db.Integer, nullable=False, default=0)
    password = db.Column(db.String(32), nullable=False)
    
    # Define relationships
    user = db.relationship('Users', foreign_keys=[user_id], lazy='joined')
    image = db.relationship('WebShellImage', foreign_keys=[image_id], lazy='joined')
    
    def __init__(self, user_id, image_id, shell_port=None, desktop_port=None):
        self.user_id = user_id
        self.image_id = image_id
        self.shell_port = shell_port
        self.desktop_port = desktop_port
        self.status = 0
        self.renew_count = 0
    
    @property
    def access_url(self):
        """
        Get the shell access URL
        """
        domain = get_config("webshell:domain", "localhost")
        protocol = "https://" if get_config("webshell:https_required", "true") == "true" else "http://"
        
        if self.shell_port:
            return f"{protocol}{domain}:{self.shell_port}"
        return None
    
    @property
    def desktop_url(self):
        """
        Get the desktop access URL
        """
        domain = get_config("webshell:domain", "localhost")
        protocol = "https://" if get_config("webshell:https_required", "true") == "true" else "http://"
        
        if self.desktop_port and self.image and self.image.has_desktop:
            return f"{protocol}{domain}:{self.desktop_port}"
        return None
    
    def is_expired(self):
        """
        Check if the container has expired
        """
        if not self.image:
            return True
            
        timeout = self.image.timeout
        return (datetime.datetime.utcnow() - self.start_time).total_seconds() > timeout
