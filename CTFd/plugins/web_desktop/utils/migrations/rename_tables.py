import datetime
from flask import current_app
from sqlalchemy import inspect, text
from CTFd.models import db

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
            
            # Rename the old table to avoid future conflicts
            db.engine.execute("ALTER TABLE desktop_container RENAME TO desktop_container_old")
            current_app.logger.info("[Web Desktop] Renamed old table to desktop_container_old")
            
            return True
        else:
            current_app.logger.info("[Web Desktop] No old desktop_container table found, no migration needed")
            return True
    except Exception as e:
        current_app.logger.error(f"[Web Desktop] Error migrating desktop_container: {str(e)}")
        return False
