import os
import random
from flask import current_app

class CacheProvider:
    def __init__(self, app=None):
        """
        Initialize the cache provider

        Args:
            app (Flask, optional): The Flask application
        """
        self.app = app
        self.available_ports = set()
        self.used_ports = set()

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize the cache provider with a Flask application

        Args:
            app (Flask): The Flask application
        """
        self.app = app

    def init_port_sets(self):
        """
        Initialize the port sets
        """
        try:
            # Get port range from config
            port_start = 10000
            port_end = 11000
            
            # Try to get from config
            try:
                port_start = int(current_app.config.get('WEB_DESKTOP_PORT_START', 10000))
                port_end = int(current_app.config.get('WEB_DESKTOP_PORT_END', 11000))
            except (ValueError, TypeError):
                port_start = 10000
                port_end = 11000
                
            # Clear existing port sets
            self.available_ports = set()
            self.used_ports = set()

            # Add all ports to available set
            for port in range(port_start, port_end + 1):
                self.available_ports.add(port)

            current_app.logger.info(f"[Web Desktop] Initialized port sets with range {port_start}-{port_end}")
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error initializing port sets: {str(e)}")

    def get_available_port(self):
        """
        Get an available port

        Returns:
            int: An available port, or None if no ports are available
        """
        try:
            # Check if there are any available ports
            if not self.available_ports:
                # If no ports are available, initialize the port sets
                current_app.logger.warning("[Web Desktop] No available ports, reinitializing port sets")
                self.init_port_sets()

            # Try to pop a port from the available set
            if not self.available_ports:
                # If still no ports, use a random port
                port = random.randint(10000, 11000)
                current_app.logger.warning(f"[Web Desktop] No available ports after reinitialization, using random port: {port}")
                return port

            port = self.available_ports.pop()

            # Add to used set
            self.used_ports.add(port)

            return port
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error getting available port: {str(e)}")
            # Fallback to random port
            port = random.randint(10000, 11000)
            current_app.logger.warning(f"[Web Desktop] Using random port due to error: {port}")
            return port

    def add_available_port(self, port):
        """
        Add a port back to the available set

        Args:
            port (int): The port to add
        """
        try:
            # Remove from used set
            if port in self.used_ports:
                self.used_ports.remove(port)

            # Add to available set
            self.available_ports.add(port)
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error adding available port: {str(e)}")

    def get_port_sets_status(self):
        """
        Get the status of the port sets

        Returns:
            dict: A dictionary with the status of the port sets
        """
        try:
            return {
                'available': len(self.available_ports),
                'used': len(self.used_ports)
            }
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error getting port sets status: {str(e)}")
            return {
                'available': 0,
                'used': 0,
                'error': str(e)
            }
