import importlib
import docker
import traceback
import datetime
import uuid
from flask import current_app

from CTFd.utils import get_config

# Importing from the whale plugin to reuse its functionality using importlib
whale_cache = importlib.import_module('CTFd.plugins.ctfd-whale.utils.cache')
whale_docker = importlib.import_module('CTFd.plugins.ctfd-whale.utils.docker')
CacheProvider = whale_cache.CacheProvider
DockerUtils = whale_docker.DockerUtils

from ..models import WebShellContainer, WebShellImage, db


class ControlUtil:
    """Utility class for controlling WebShell containers - with HTTP instead of HTTPS for better compatibility"""
    
    @staticmethod
    def try_add_container(user_id, image_id):
        """
        Create a new WebShell container
        
        Args:
            user_id: User ID
            image_id: WebShell image ID
            
        Returns:
            (success, message, container_obj)
        """
        current_app.logger.info(f"[WebShell] Creating container for user {user_id} with image {image_id}")
        
        # Get the image configuration
        image = WebShellImage.query.filter_by(id=image_id).first()
        if not image:
            current_app.logger.warning(f"[WebShell] Invalid image ID: {image_id}")
            return False, "Invalid image ID", None
        
        # Get available ports from the whale cache provider
        cache = CacheProvider(app=current_app)
        
        # We only need one port (6901) for desktop access
        desktop_port = cache.get_available_port()
        if not desktop_port:
            current_app.logger.warning("[WebShell] No available ports for desktop")
            return False, "No available ports for desktop. Please try again later.", None
        
        current_app.logger.info(f"[WebShell] Allocated port: {desktop_port}")
        
        try:
            # Create container record
            container = WebShellContainer(
                user_id=user_id,
                image_id=image_id,
                shell_port=desktop_port,  # For compatibility, use same port
                desktop_port=desktop_port
            )
            
            # Set UUID and password
            container.uuid = str(uuid.uuid4())
            container.password = "password"  # Fixed password for simplicity
            
            current_app.logger.info(f"[WebShell] Container DB record created for user {user_id}")
            
            # Add to database
            db.session.add(container)
            db.session.commit()
            
            # Create the actual Docker container
            try:
                current_app.logger.info(f"[WebShell] Creating Docker container for user {user_id}")
                ControlUtil._create_container(container)
                current_app.logger.info(f"[WebShell] Docker container created successfully for user {user_id}")
                return True, "Container created successfully", container
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Error creating Docker container: {str(e)}")
                db.session.delete(container)
                db.session.commit()
                
                # Return port to the pool
                cache.add_available_port(desktop_port)
                
                return False, f"Error creating Docker container: {str(e)}", None
            
        except Exception as e:
            # Rollback on error
            current_app.logger.exception(f"[WebShell] Error in container creation: {str(e)}")
            db.session.rollback()
            
            # Return ports to the pool
            cache.add_available_port(desktop_port)
                
            return False, f"Error creating container: {str(e)}", None
    
    @staticmethod
    def try_remove_container(user_id):
        """
        Remove a user's WebShell container
        
        Args:
            user_id: User ID
            
        Returns:
            (success, message)
        """
        current_app.logger.info(f"[WebShell] Removing container for user {user_id}")
        
        container = WebShellContainer.query.filter_by(user_id=user_id).first()
        if not container:
            current_app.logger.warning(f"[WebShell] No container found for user {user_id}")
            return False, "No container found for this user"
        
        try:
            # Remove Docker container
            current_app.logger.info(f"[WebShell] Removing Docker container for user {user_id}")
            ControlUtil._remove_container(container)
            current_app.logger.info(f"[WebShell] Docker container removed for user {user_id}")
            
            # Free up ports
            cache = CacheProvider(app=current_app)
            if container.desktop_port:
                current_app.logger.info(f"[WebShell] Returning port {container.desktop_port} to pool")
                cache.add_available_port(container.desktop_port)
            
            # Remove DB record
            current_app.logger.info(f"[WebShell] Removing DB record for user {user_id}")
            db.session.delete(container)
            db.session.commit()
            
            return True, "Container removed successfully"
            
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Error removing container: {str(e)}")
            traceback.print_exc()
            return False, f"Error removing container: {str(e)}"
            
    @staticmethod
    def try_renew_container(user_id):
        """
        Renew a user's WebShell container timeout
        
        Args:
            user_id: User ID
            
        Returns:
            (success, message)
        """
        current_app.logger.info(f"[WebShell] Renewing container for user {user_id}")
        
        container = WebShellContainer.query.filter_by(user_id=user_id).first()
        if not container:
            current_app.logger.warning(f"[WebShell] No container found for user {user_id}")
            return False, "No container found for this user"
        
        # Get container timeout from image config
        timeout = container.image.timeout
        
        # Update container start time
        current_app.logger.info(f"[WebShell] Updating container start time for user {user_id}")
        container.start_time = datetime.datetime.utcnow()
        container.renew_count += 1
        
        try:
            db.session.commit()
            current_app.logger.info(f"[WebShell] Container renewed for user {user_id}")
            return True, f"Container renewed for {timeout} seconds"
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Error renewing container: {str(e)}")
            db.session.rollback()
            return False, f"Error renewing container: {str(e)}"
            
    @staticmethod
    def _create_container(container):
        """
        Create a Docker container for WebShell - using HTTP instead of HTTPS
        
        Args:
            container: WebShellContainer object
        """
        current_app.logger.info(f"[WebShell] Creating Docker container for user {container.user_id} with image {container.image.docker_image}")
        
        # Initialize Docker client using whale's config
        docker_api_url = get_config("whale:docker_api_url", "unix:///var/run/docker.sock")
        client = docker.DockerClient(base_url=docker_api_url)
        current_app.logger.info(f"[WebShell] Connected to Docker API: {docker_api_url}")
        
        # Get container configuration
        image = container.image
        container_name = f"webshell-{container.user_id}-{container.uuid}"
        
        # Prepare environment variables for desktop compatibility
        # IMPORTANT: Using HTTP instead of HTTPS for better compatibility
        environment = {
            "PASSWORD": container.password,
            "USER_ID": str(container.user_id),
            "VNC_PW": container.password,
            "KASM_VNC_PW": container.password,
            "KASM_USER": "kasm_user",
            "LANG": "en_US.UTF-8",
            "LANGUAGE": "en_US:en",
            "LC_ALL": "en_US.UTF-8",
            "DISABLE_PROGRESS": "true",
            "KASM_SERVER_HOSTNAME": "localhost",  # Force localhost
            "SSL_ENABLED": "false",  # Disable SSL to avoid certificate issues
            "SECURE_CONNECTION": "false",  # Disable HTTPS to avoid certificate issues
            "CONTAINER_MOUNTED": "true",
            "FLAG": f"CTF{{webshell_{container.uuid}}}"
        }
        
        current_app.logger.info(f"[WebShell] Container environment prepared for user {container.user_id}")
        
        # Prepare ports mapping for Docker API - use port 6901 for desktop access
        port_bindings = []
        if container.desktop_port > 0:
            port_bindings.append({
                'published_port': container.desktop_port,
                'target_port': 6901,  # Web interface port
                'protocol': 'tcp'
            })
        
        current_app.logger.info(f"[WebShell] Port binding: {container.desktop_port}:6901")
            
        # Set resource limits
        mem_limit = DockerUtils.convert_readable_text(image.memory_limit)
        cpu_limit = int(float(image.cpu_limit) * 1e9)  # Convert to nano CPUs
        
        # Prepare DNS configuration
        dns = get_config("whale:docker_dns", "").split(",")
        dns = [d for d in dns if d]  # Filter empty strings
        
        # Create the container using Swarm mode
        network = get_config("whale:docker_auto_connect_network", "ctfd_frp-containers")
        
        # Select appropriate node - using CTFd-whale's node selection
        node = DockerUtils.choose_node(
            image.docker_image,
            get_config("whale:docker_swarm_nodes", "").split(",")
        )
        
        current_app.logger.info(f"[WebShell] Selected node: {node}")
        
        # Create service (swarm mode container) configured for Kasm
        try:
            current_app.logger.info(f"[WebShell] Creating Docker service: {container_name}")
            service = client.services.create(
                image=image.docker_image,
                name=container_name,
                env=environment,
                networks=[network],
                endpoint_spec=docker.types.EndpointSpec(
                    ports=port_bindings
                ),
                resources=docker.types.Resources(
                    mem_limit=mem_limit,
                    cpu_limit=cpu_limit
                ),
                labels={
                    'webshell_id': f'{container.user_id}-{container.uuid}',
                    'plugin': 'webshell',
                    'kasm_enabled': 'true',
                    'whale_id': f'{container.user_id}-{container.uuid}'  # Use whale_id for compatibility
                },
                constraints=[f'node.labels.name=={node}'],
                dns_config=docker.types.DNSConfig(nameservers=dns) if dns else None,
                mounts=[
                    # Mount shared memory to allow Kasm to run properly
                    docker.types.Mount(
                        target='/dev/shm',
                        source=None,  # Docker creates an anonymous volume
                        type='tmpfs',
                        read_only=False,
                        tmpfs_size=536870912  # 512MB (in bytes)
                    )
                ]
            )
            current_app.logger.info(f"[WebShell] Docker service created: {service.id}")
            return service
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Error creating Docker service: {str(e)}")
            raise e
    
    @staticmethod
    def _remove_container(container):
        """
        Remove a Docker container
        
        Args:
            container: WebShellContainer object
        """
        current_app.logger.info(f"[WebShell] Removing Docker container for user {container.user_id}")
        
        # Initialize Docker client
        docker_api_url = get_config("whale:docker_api_url", "unix:///var/run/docker.sock")
        client = docker.DockerClient(base_url=docker_api_url)
        current_app.logger.info(f"[WebShell] Connected to Docker API: {docker_api_url}")
        
        webshell_id = f'{container.user_id}-{container.uuid}'
        current_app.logger.info(f"[WebShell] Looking for services with label webshell_id={webshell_id}")
        
        # Find and remove services with matching webshell_id label
        for service in client.services.list(filters={'label': f'webshell_id={webshell_id}'}):
            current_app.logger.info(f"[WebShell] Removing service: {service.id}")
            service.remove()
