import importlib
from flask import current_app

from ..models import DesktopContainer, DesktopTemplate, DesktopConfig, db

# Import whale plugin components using importlib to avoid syntax issues with hyphens
try:
    whale_db = importlib.import_module('CTFd.plugins.ctfd-whale.utils.db')
    if hasattr(whale_db, 'DBContainer'): 
        WhaleDBContainer = whale_db.DBContainer
    else:
        current_app.logger.error("[Web Desktop] whale_db does not have DBContainer attribute")
        WhaleDBContainer = None
except ImportError as e:
    current_app.logger.error(f"[Web Desktop] Error importing CTFd-whale components: {str(e)}")
    WhaleDBContainer = None
except Exception as e:
    current_app.logger.error(f"[Web Desktop] Unexpected error with whale_db: {str(e)}")
    WhaleDBContainer = None

class DBContainer:
    @staticmethod
    def get_current_containers(user_id=None):
        """
        Get the current container for a user

        Args:
            user_id (int, optional): The user ID

        Returns:
            DesktopContainer: The container record, or None if not found
        """
        if user_id is None:
            return None

        # Try to get the whale container first
        if WhaleDBContainer:
            try:
                whale_container = WhaleDBContainer.get_current_containers(user_id)
                if whale_container:
                    # Get the corresponding desktop container
                    desktop_container = DesktopContainer.query.filter_by(user_id=user_id).first()
                    if desktop_container:
                        return desktop_container
                    else:
                        # Create a desktop container record if it doesn't exist
                        desktop_container = DesktopContainer(
                            user_id=user_id,
                            template_id=0,  # Default template ID
                            port=whale_container.port
                        )
                        db.session.add(desktop_container)
                        db.session.commit()
                        return desktop_container
            except Exception as e:
                current_app.logger.error(f"[Web Desktop] Error getting whale container: {str(e)}")

        # Fallback to desktop container
        return DesktopContainer.query.filter_by(user_id=user_id).first()

    @staticmethod
    def get_all_container():
        """
        Get all containers

        Returns:
            list: A list of all container records
        """
        return DesktopContainer.query.all()

    @staticmethod
    def get_all_alive_container_count():
        """
        Get the count of all alive containers

        Returns:
            int: The count of alive containers
        """
        return DesktopContainer.query.count()

    @staticmethod
    def get_all_alive_container_page(page_start, page_end):
        """
        Get a page of alive containers

        Args:
            page_start (int): The start index
            page_end (int): The end index

        Returns:
            list: A list of container records
        """
        try:
            containers = DesktopContainer.query.slice(page_start, page_end).all()
            return containers
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error getting containers: {str(e)}")
            return []

    @staticmethod
    def remove_container_record(user_id):
        """
        Remove a container record for a user

        Args:
            user_id (int): The user ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            container = DesktopContainer.query.filter_by(user_id=user_id).first()
            if not container:
                return False

            db.session.delete(container)
            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error removing container record: {str(e)}")
            return False

class DBConfig:
    @staticmethod
    def get_config(key, default=None):
        """
        Get a configuration value

        Args:
            key (str): The configuration key
            default (any, optional): The default value if not found

        Returns:
            str: The configuration value
        """
        try:
            config = DesktopConfig.query.filter_by(key=key).first()
            if config:
                return config.value
            return default
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error getting config {key}: {str(e)}")
            return default

    @staticmethod
    def get_all_configs():
        """
        Get all configuration values

        Returns:
            dict: A dictionary of all configuration values
        """
        try:
            configs = DesktopConfig.query.all()
            return {config.key: config.value for config in configs}
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error getting all configs: {str(e)}")
            return {}

    @staticmethod
    def set_config(key, value):
        """
        Set a configuration value

        Args:
            key (str): The configuration key
            value (str): The configuration value

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = DesktopConfig.query.filter_by(key=key).first()
            if config:
                config.value = value
            else:
                config = DesktopConfig(key=key, value=value)
                db.session.add(config)
            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error setting config {key}: {str(e)}")
            return False
