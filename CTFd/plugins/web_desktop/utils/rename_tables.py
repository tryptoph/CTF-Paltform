import datetime
from flask import current_app
from sqlalchemy import inspect, text
from CTFd.models import db

def migrate_old_tables():
    """
    Migrate data from all old tables to new tables if needed
    """
    # Migrate each table
    migrate_desktop_container()
    migrate_desktop_template()
    migrate_desktop_config()
    migrate_challenge_desktop_link()

    return True

def migrate_desktop_template():
    """
    Migrate data from desktop_template to web_desktop_templates if needed
    """
    try:
        # Check if old table exists
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'desktop_template' in tables:
            current_app.logger.info("[Web Desktop] Found old desktop_template table, checking for data to migrate")

            try:
                # Check if there's data to migrate
                result = db.engine.execute("SELECT COUNT(*) FROM desktop_template")
                count = result.scalar()

                if count > 0:
                    current_app.logger.info(f"[Web Desktop] Found {count} records to migrate from desktop_template")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not query desktop_template table: {str(inner_e)}")
                count = 0

            try:
                # Rename the old table to avoid future conflicts
                if db.engine.name == 'sqlite':
                    db.engine.execute("ALTER TABLE desktop_template RENAME TO desktop_template_old")
                elif db.engine.name == 'mysql' or db.engine.name == 'mariadb':
                    db.engine.execute("RENAME TABLE desktop_template TO desktop_template_old")
                else:
                    db.engine.execute("ALTER TABLE desktop_template RENAME TO desktop_template_old")

                current_app.logger.info("[Web Desktop] Renamed old table to desktop_template_old")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not rename desktop_template table: {str(inner_e)}")

            return True
        else:
            current_app.logger.info("[Web Desktop] No old desktop_template table found, no migration needed")
            return True
    except Exception as e:
        current_app.logger.error(f"[Web Desktop] Error migrating desktop_template: {str(e)}")
        # Return True to continue with other migrations even if this one fails
        return True

def migrate_desktop_config():
    """
    Migrate data from desktop_config to web_desktop_config if needed
    """
    try:
        # Check if old table exists
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'desktop_config' in tables:
            current_app.logger.info("[Web Desktop] Found old desktop_config table, checking for data to migrate")

            try:
                # Check if there's data to migrate
                result = db.engine.execute("SELECT COUNT(*) FROM desktop_config")
                count = result.scalar()

                if count > 0:
                    current_app.logger.info(f"[Web Desktop] Found {count} records to migrate from desktop_config")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not query desktop_config table: {str(inner_e)}")
                count = 0

            try:
                # Rename the old table to avoid future conflicts
                if db.engine.name == 'sqlite':
                    db.engine.execute("ALTER TABLE desktop_config RENAME TO desktop_config_old")
                elif db.engine.name == 'mysql' or db.engine.name == 'mariadb':
                    db.engine.execute("RENAME TABLE desktop_config TO desktop_config_old")
                else:
                    db.engine.execute("ALTER TABLE desktop_config RENAME TO desktop_config_old")

                current_app.logger.info("[Web Desktop] Renamed old table to desktop_config_old")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not rename desktop_config table: {str(inner_e)}")

            return True
        else:
            current_app.logger.info("[Web Desktop] No old desktop_config table found, no migration needed")
            return True
    except Exception as e:
        current_app.logger.error(f"[Web Desktop] Error migrating desktop_config: {str(e)}")
        # Return True to continue with other migrations even if this one fails
        return True

def migrate_challenge_desktop_link():
    """
    Migrate data from challenge_desktop_link to web_desktop_challenge_links if needed
    """
    try:
        # Check if old table exists
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'challenge_desktop_link' in tables:
            current_app.logger.info("[Web Desktop] Found old challenge_desktop_link table, checking for data to migrate")

            try:
                # Check if there's data to migrate
                result = db.engine.execute("SELECT COUNT(*) FROM challenge_desktop_link")
                count = result.scalar()

                if count > 0:
                    current_app.logger.info(f"[Web Desktop] Found {count} records to migrate from challenge_desktop_link")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not query challenge_desktop_link table: {str(inner_e)}")
                count = 0

            try:
                # Rename the old table to avoid future conflicts
                if db.engine.name == 'sqlite':
                    db.engine.execute("ALTER TABLE challenge_desktop_link RENAME TO challenge_desktop_link_old")
                elif db.engine.name == 'mysql' or db.engine.name == 'mariadb':
                    db.engine.execute("RENAME TABLE challenge_desktop_link TO challenge_desktop_link_old")
                else:
                    db.engine.execute("ALTER TABLE challenge_desktop_link RENAME TO challenge_desktop_link_old")

                current_app.logger.info("[Web Desktop] Renamed old table to challenge_desktop_link_old")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not rename challenge_desktop_link table: {str(inner_e)}")

            return True
        else:
            current_app.logger.info("[Web Desktop] No old challenge_desktop_link table found, no migration needed")
            return True
    except Exception as e:
        current_app.logger.error(f"[Web Desktop] Error migrating challenge_desktop_link: {str(e)}")
        # Return True to continue with other migrations even if this one fails
        return True

def migrate_desktop_container():
    """
    Migrate data from desktop_container to web_desktop_containers if needed
    """
    try:
        # Check if old table exists
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'desktop_container' in tables:
            current_app.logger.info("[Web Desktop] Found old desktop_container table, checking for data to migrate")

            # Check if the new table exists
            if 'web_desktop_containers' not in tables:
                current_app.logger.info("[Web Desktop] Creating new web_desktop_containers table")
                # Create the new table
                if db.engine.name == 'sqlite':
                    db.engine.execute("""
                    CREATE TABLE web_desktop_containers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        template_id INTEGER,
                        start_time DATETIME NOT NULL,
                        renew_count INTEGER NOT NULL DEFAULT 0,
                        status INTEGER DEFAULT 1,
                        uuid VARCHAR(256),
                        port INTEGER DEFAULT 0,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(template_id) REFERENCES web_desktop_templates(id)
                    )
                    """)
                elif db.engine.name == 'mysql' or db.engine.name == 'mariadb':
                    db.engine.execute("""
                    CREATE TABLE web_desktop_containers (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        user_id INTEGER,
                        template_id INTEGER,
                        start_time DATETIME NOT NULL,
                        renew_count INTEGER NOT NULL DEFAULT 0,
                        status INTEGER DEFAULT 1,
                        uuid VARCHAR(256),
                        port INTEGER DEFAULT 0,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(template_id) REFERENCES web_desktop_templates(id)
                    )
                    """)
                else:
                    # Generic approach - let SQLAlchemy create it
                    from ..models import DesktopContainer
                    DesktopContainer.__table__.create(db.engine)

            try:
                # Check if there's data to migrate
                result = db.engine.execute("SELECT COUNT(*) FROM desktop_container")
                count = result.scalar()

                if count > 0:
                    current_app.logger.info(f"[Web Desktop] Found {count} records to migrate from desktop_container")

                    # Migrate data
                    db.engine.execute("""
                    INSERT INTO web_desktop_containers (user_id, template_id, start_time, renew_count, status, uuid, port)
                    SELECT user_id, template_id, start_time, renew_count, status, uuid, port
                    FROM desktop_container
                    """)

                    current_app.logger.info("[Web Desktop] Data migration completed")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not query desktop_container table: {str(inner_e)}")

            try:
                # Rename the old table to avoid future conflicts
                if db.engine.name == 'sqlite':
                    db.engine.execute("ALTER TABLE desktop_container RENAME TO desktop_container_old")
                elif db.engine.name == 'mysql' or db.engine.name == 'mariadb':
                    db.engine.execute("RENAME TABLE desktop_container TO desktop_container_old")
                else:
                    db.engine.execute("ALTER TABLE desktop_container RENAME TO desktop_container_old")

                current_app.logger.info("[Web Desktop] Renamed old table to desktop_container_old")
            except Exception as inner_e:
                current_app.logger.warning(f"[Web Desktop] Could not rename desktop_container table: {str(inner_e)}")

            return True
        else:
            current_app.logger.info("[Web Desktop] No old desktop_container table found, no migration needed")
            return True
    except Exception as e:
        current_app.logger.error(f"[Web Desktop] Error migrating desktop_container: {str(e)}")
        # Return True to continue with other migrations even if this one fails
        return True
