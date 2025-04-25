from CTFd.models import db
from ..models import DesktopTemplate, DesktopConfig, ChallengeDesktopLink, DesktopContainer
from .rename_tables import migrate_old_tables

def upgrade():
    """
    Upgrade the database schema for the Web Desktop plugin
    """
    # First, check for old tables and migrate if needed
    migrate_old_tables()

    # Create tables if they don't exist
    if not db.engine.dialect.has_table(db.engine, "web_desktop_templates"):
        DesktopTemplate.__table__.create(db.engine)

    if not db.engine.dialect.has_table(db.engine, "web_desktop_config"):
        DesktopConfig.__table__.create(db.engine)

    if not db.engine.dialect.has_table(db.engine, "web_desktop_challenge_links"):
        ChallengeDesktopLink.__table__.create(db.engine)

    if not db.engine.dialect.has_table(db.engine, "web_desktop_containers"):
        DesktopContainer.__table__.create(db.engine)

    # Add default template if none exist
    if DesktopTemplate.query.count() == 0:
        default_template = DesktopTemplate(
            name="Kali Linux Desktop",
            description="Kali Linux desktop environment with common penetration testing tools",
            docker_image="kasmweb/kali-rolling-desktop:1.14.0",
            memory_limit="512m",
            cpu_limit=2.0,
            desktop_port=6901,
            is_enabled=True,
            icon="kali-logo.svg",
            display_order=0,
            connection_type="direct",
            recommended=True
        )
        db.session.add(default_template)
        db.session.commit()

def downgrade():
    """
    Downgrade the database schema for the Web Desktop plugin
    """
    # Drop tables in reverse order of dependencies
    ChallengeDesktopLink.__table__.drop(db.engine)
    DesktopContainer.__table__.drop(db.engine)
    DesktopConfig.__table__.drop(db.engine)
    DesktopTemplate.__table__.drop(db.engine)
