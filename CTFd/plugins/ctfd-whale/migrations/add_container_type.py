import datetime
from flask import current_app
from sqlalchemy import Column, String, text, inspect
from CTFd.models import db

def upgrade():
    """
    Add container_type column to WhaleContainer table
    """
    try:
        # Use SQLAlchemy's inspect to check if column exists
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('whale_container')]
        exists = 'container_type' in columns

        if not exists:
            # Add the container_type column with default value 'challenge'
            # Use different syntax for different database types
            if db.engine.name == 'mysql' or db.engine.name == 'mariadb':
                db.engine.execute('ALTER TABLE whale_container ADD COLUMN container_type VARCHAR(20) NOT NULL DEFAULT "challenge"')
            elif db.engine.name == 'postgresql':
                db.engine.execute("ALTER TABLE whale_container ADD COLUMN container_type VARCHAR(20) NOT NULL DEFAULT 'challenge'")
            elif db.engine.name == 'sqlite':
                db.engine.execute("ALTER TABLE whale_container ADD COLUMN container_type VARCHAR(20) NOT NULL DEFAULT 'challenge'")
            else:
                # Generic approach
                db.engine.execute("ALTER TABLE whale_container ADD COLUMN container_type VARCHAR(20) NOT NULL DEFAULT 'challenge'")

            current_app.logger.info(f"[CTFd-Whale] Added container_type column to whale_container table using {db.engine.name} syntax")
        else:
            current_app.logger.info("[CTFd-Whale] container_type column already exists in whale_container table")
        return True
    except Exception as e:
        current_app.logger.error(f"[CTFd-Whale] Error adding container_type column: {str(e)}")
        return False
