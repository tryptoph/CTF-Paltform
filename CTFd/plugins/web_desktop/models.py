import random
import uuid
from datetime import datetime

from jinja2 import Template
from CTFd.models import db, Users, Challenges
from CTFd.utils import get_config
from sqlalchemy.exc import OperationalError, ProgrammingError

# Function to create all tables
def create_all():
    """Create all database tables for the web_desktop plugin"""
    try:
        # Create tables if they don't exist
        DesktopTemplate.__table__.create(db.engine, checkfirst=True)
        DesktopConfig.__table__.create(db.engine, checkfirst=True)
        DesktopContainer.__table__.create(db.engine, checkfirst=True)
        ChallengeDesktopLink.__table__.create(db.engine, checkfirst=True)
        return True
    except (OperationalError, ProgrammingError) as e:
        print(f"Error creating web_desktop tables: {str(e)}")
        return False

class DesktopTemplate(db.Model):
    __tablename__ = "web_desktop_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    docker_image = db.Column(db.String(255), nullable=False)
    memory_limit = db.Column(db.String(20), default="512m")
    cpu_limit = db.Column(db.Float, default=2.0)
    desktop_port = db.Column(db.Integer, default=6901)
    is_enabled = db.Column(db.Boolean, default=True)
    # Additional fields for UI/UX
    icon = db.Column(db.String(128), default="desktop-icon.svg")
    display_order = db.Column(db.Integer, default=0)
    connection_type = db.Column(db.String(20), default="direct")
    recommended = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(DesktopTemplate, self).__init__(**kwargs)

class DesktopConfig(db.Model):
    __tablename__ = "web_desktop_config"

    key = db.Column(db.String(length=128), primary_key=True)
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<DesktopConfig {0} {1}>".format(self.key, self.value)

class DesktopContainer(db.Model):
    __tablename__ = "web_desktop_containers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(None, db.ForeignKey("users.id"))
    template_id = db.Column(None, db.ForeignKey("web_desktop_templates.id"))
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    renew_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Integer, default=1)
    uuid = db.Column(db.String(256))
    port = db.Column(db.Integer, nullable=True, default=0)

    # Relationships
    user = db.relationship("Users", foreign_keys="DesktopContainer.user_id", lazy="select")
    template = db.relationship("DesktopTemplate", foreign_keys="DesktopContainer.template_id", lazy="select")

    @property
    def http_subdomain(self):
        return Template(get_config(
            'web_desktop:template_http_subdomain', '{{ container.uuid }}'
        )).render(container=self)

    def __init__(self, user_id, template_id, port):
        self.user_id = user_id
        self.template_id = template_id
        self.start_time = datetime.now()
        self.renew_count = 0
        self.uuid = str(uuid.uuid4())
        self.port = port

    @property
    def user_access(self):
        # Direct access to desktop via port
        domain = get_config("web_desktop:domain", "localhost")
        protocol = "https://" if get_config("web_desktop:https_required", "true") == "true" else "http://"
        return f"{protocol}{domain}:{self.port}"

    def __repr__(self):
        return "<DesktopContainer ID:{0} {1} {2} {3} {4}>".format(self.id, self.user_id, self.template_id,
                                                                self.start_time, self.renew_count)

class ChallengeDesktopLink(db.Model):
    __tablename__ = "web_desktop_challenge_links"

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("web_desktop_templates.id"), nullable=False)

    challenge = db.relationship("Challenges", foreign_keys="ChallengeDesktopLink.challenge_id", lazy="select")
    template = db.relationship("DesktopTemplate", foreign_keys="ChallengeDesktopLink.template_id", lazy="select")
