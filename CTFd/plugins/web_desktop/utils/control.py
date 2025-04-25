import datetime
import traceback
import docker
import importlib
from flask import current_app

from CTFd.utils import get_config
from .cache import CacheProvider
from ..models import DesktopContainer, DesktopTemplate, ChallengeDesktopLink, db

# Import whale plugin components using importlib to avoid syntax issues with hyphens
try:
    whale_models = importlib.import_module('CTFd.plugins.ctfd-whale.models')
    WhaleContainer = whale_models.WhaleContainer
    DynamicDockerChallenge = whale_models.DynamicDockerChallenge

    whale_control = importlib.import_module('CTFd.plugins.ctfd-whale.utils.control')
    WhaleControlUtil = whale_control.ControlUtil

    whale_db = importlib.import_module('CTFd.plugins.ctfd-whale.utils.db')
    WhaleDBContainer = None
    if hasattr(whale_db, 'DBContainer'):
        WhaleDBContainer = whale_db.DBContainer
except ImportError as e:
    current_app.logger.error(f"[Web Desktop] Error importing CTFd-whale components: {str(e)}")
    WhaleContainer = None
    DynamicDockerChallenge = None
    WhaleControlUtil = None
    WhaleDBContainer = None
except AttributeError as e:
    current_app.logger.error(f"[Web Desktop] Error accessing CTFd-whale components: {str(e)}")
    if 'WhaleContainer' not in locals():
        WhaleContainer = None
    if 'DynamicDockerChallenge' not in locals():
        DynamicDockerChallenge = None
    if 'WhaleControlUtil' not in locals():
        WhaleControlUtil = None
    if 'WhaleDBContainer' not in locals():
        WhaleDBContainer = None

class ControlUtil:
    @staticmethod
    def try_add_container(user_id, template_id):
        """
        Try to add a new container for a user with the specified template

        Args:
            user_id (int): The user ID
            template_id (int): The template ID

        Returns:
            tuple: (success, message)
        """
        # Check if whale plugin is available
        if not WhaleControlUtil or not DynamicDockerChallenge:
            current_app.logger.error("[Web Desktop] CTFd-whale components not available")
            return False, 'Container management system not available. Please contact an administrator.'

        try:
            # First, remove any existing container for this user
            try:
                existing_container = WhaleContainer.query.filter_by(user_id=user_id).first()
                if existing_container:
                    ControlUtil.try_remove_container(user_id)
            except Exception as e:
                current_app.logger.error(f"[Web Desktop] Error removing existing container: {str(e)}")

            # Get template
            template = DesktopTemplate.query.filter_by(id=template_id).first()
            if not template:
                return False, 'Invalid template'

            # Ensure the user network exists first
            try:
                # Import docker module and DockerUtils directly
                docker_utils = importlib.import_module('CTFd.plugins.ctfd-whale.utils.docker')
                DockerUtils = docker_utils.DockerUtils
                docker_types = importlib.import_module('docker.types')
                cache_provider = importlib.import_module('CTFd.plugins.ctfd-whale.utils.cache')
                CacheProvider = cache_provider.CacheProvider

                # Check if user network exists
                network_name = f'user-{user_id}-network'
                client = DockerUtils.client
                networks = client.networks.list(names=[network_name])

                if not networks:
                    current_app.logger.info(f"[Web Desktop] User network not found. Creating network {network_name}")

                    # Get a network range from the cache
                    range_prefix = CacheProvider(app=current_app).get_available_network_range()
                    ipam_pool = docker_types.IPAMPool(subnet=range_prefix)
                    ipam_config = docker_types.IPAMConfig(driver='default', pool_configs=[ipam_pool])

                    # Create the network explicitly before trying to create the container
                    network = client.networks.create(
                        network_name,
                        internal=True,
                        ipam=ipam_config,
                        attachable=True,
                        labels={'prefix': range_prefix, 'user_id': str(user_id)},
                        driver="overlay",
                        scope="swarm"
                    )
                    current_app.logger.info(f"[Web Desktop] Successfully created network {network_name}")
            except Exception as net_err:
                current_app.logger.error(f"[Web Desktop] Error ensuring user network exists: {str(net_err)}")
                # Continue anyway, as the container creation code might handle this

            # Check if a challenge exists for this template, create one if not
            challenge = DynamicDockerChallenge.query.filter_by(
                docker_image=template.docker_image,
                category="Web Desktop"
            ).first()

            if not challenge:
                # Create a challenge for this template
                challenge = DynamicDockerChallenge(
                    name=f"Web Desktop - {template.name}",
                    description=template.description or "Web Desktop Environment",
                    value=0,
                    initial=0,  # Required for dynamic challenges
                    decay=0,    # Required for dynamic challenges
                    minimum=0,  # Required for dynamic challenges
                    category="Web Desktop",
                    type="dynamic_docker",
                    state="hidden",  # Hide from challenges page
                    docker_image=template.docker_image,
                    memory_limit=template.memory_limit,
                    cpu_limit=template.cpu_limit,
                    redirect_type="direct",  # Use direct connection
                    redirect_port=template.desktop_port  # Use the desktop port from the template
                )
                db.session.add(challenge)
                db.session.commit()
                current_app.logger.info(f"[Web Desktop] Created challenge for template: {template.name}")

                # Create a link between the challenge and the template
                link = ChallengeDesktopLink(
                    challenge_id=challenge.id,
                    template_id=template.id
                )
                db.session.add(link)
                db.session.commit()
                current_app.logger.info(f"[Web Desktop] Created link between challenge and template: {template.name}")

            # Use whale plugin to create container with desktop container type - with retry logic
            retry_count = 0
            max_retries = 3
            last_error = None
            success = False

            while retry_count < max_retries and not success:
                try:
                    result, message = WhaleControlUtil.try_add_container(user_id, challenge.id, container_type="desktop")
                    if result:
                        success = True
                        break
                    else:
                        # Check if the error contains network related issues
                        if "network" in message.lower():
                            current_app.logger.warning(f"[Web Desktop] Network error during container creation (attempt {retry_count+1}/{max_retries}): {message}")
                            # If network issue, try to fix it before retrying
                            try:
                                # Try to recreate the network
                                docker_utils = importlib.import_module('CTFd.plugins.ctfd-whale.utils.docker')
                                DockerUtils = docker_utils.DockerUtils
                                docker_types = importlib.import_module('docker.types')
                                cache_provider = importlib.import_module('CTFd.plugins.ctfd-whale.utils.cache')
                                CacheProvider = cache_provider.CacheProvider

                                # Force network cleanup and recreation
                                network_name = f'user-{user_id}-network'
                                client = DockerUtils.client
                                networks = client.networks.list(names=[network_name])

                                # Remove any existing network with that name
                                for network in networks:
                                    try:
                                        network.remove()
                                        current_app.logger.info(f"[Web Desktop] Removed problematic network {network_name}")
                                    except Exception:
                                        pass

                                # Create a new network
                                range_prefix = CacheProvider(app=current_app).get_available_network_range()
                                ipam_pool = docker_types.IPAMPool(subnet=range_prefix)
                                ipam_config = docker_types.IPAMConfig(driver='default', pool_configs=[ipam_pool])

                                network = client.networks.create(
                                    network_name,
                                    internal=True,
                                    ipam=ipam_config,
                                    attachable=True,
                                    labels={'prefix': range_prefix, 'user_id': str(user_id)},
                                    driver="overlay",
                                    scope="swarm"
                                )
                                current_app.logger.info(f"[Web Desktop] Successfully recreated network {network_name}")
                            except Exception as network_err:
                                current_app.logger.error(f"[Web Desktop] Failed to fix network: {str(network_err)}")

                        last_error = message
                except Exception as container_err:
                    current_app.logger.error(f"[Web Desktop] Error in container creation (attempt {retry_count+1}/{max_retries}): {str(container_err)}")
                    last_error = str(container_err)

                # Increment retry counter
                retry_count += 1
                if retry_count < max_retries and not success:
                    # Wait briefly before retrying
                    import time
                    time.sleep(1.5)

            # Check if we succeeded after retries
            if not success:
                if "network" in str(last_error).lower():
                    current_app.logger.error(f"[Web Desktop] Failed after {max_retries} attempts to create container due to network issues")
                    return False, f'Network error: Unable to create container after multiple attempts. Please try again later.'
                return False, f'Failed to create container: {last_error}'

            # Get the container that was just created
            whale_container = WhaleContainer.query.filter_by(user_id=user_id, container_type="desktop").first()
            if not whale_container:
                return False, 'Container created but not found in database'

            # Check if a desktop container record already exists for this user
            desktop_container = DesktopContainer.query.filter_by(user_id=user_id).first()
            if desktop_container:
                # Update existing record
                desktop_container.template_id = template_id
                desktop_container.port = whale_container.port
                desktop_container.start_time = datetime.datetime.now()
                desktop_container.renew_count = 0
            else:
                # Create a new desktop container record linked to the whale container
                desktop_container = DesktopContainer(
                    user_id=user_id,
                    template_id=template_id,
                    port=whale_container.port
                )
                db.session.add(desktop_container)

            db.session.commit()
            return True, 'Container created successfully'
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error creating container: {str(e)}")
            traceback.print_exc()
            return False, f'Error creating container: {str(e)}'

    @staticmethod
    def try_remove_container(user_id):
        """
        Try to remove a container for a user

        Args:
            user_id (int): The user ID

        Returns:
            tuple: (success, message)
        """
        # Check if whale plugin is available
        if not WhaleControlUtil:
            current_app.logger.error("[Web Desktop] CTFd-whale components not available")
            return False, 'Container management system not available. Please contact an administrator.'

        try:
            # Get the desktop container for this user
            desktop_container = DesktopContainer.query.filter_by(user_id=user_id).first()

            # Use whale plugin to remove container
            result, message = WhaleControlUtil.try_remove_container(user_id, container_type="desktop")

            # If we have a desktop container, remove it too
            if desktop_container:
                db.session.delete(desktop_container)
                db.session.commit()

            return result, message
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error removing container: {str(e)}")
            traceback.print_exc()
            return False, f'Error removing container: {str(e)}'

    @staticmethod
    def try_renew_container(user_id):
        """
        Try to renew a container for a user

        Args:
            user_id (int): The user ID

        Returns:
            tuple: (success, message)
        """
        # Check if whale plugin is available
        if not WhaleControlUtil:
            current_app.logger.error("[Web Desktop] CTFd-whale components not available")
            return False, 'Container management system not available. Please contact an administrator.'

        try:
            # Get the desktop container for this user
            desktop_container = DesktopContainer.query.filter_by(user_id=user_id).first()

            # Get the whale container
            whale_container = WhaleContainer.query.filter_by(user_id=user_id, container_type="desktop").first()
            if not whale_container:
                return False, 'No container found to renew'

            # Use whale plugin to renew container
            result, message = WhaleControlUtil.try_renew_container(user_id, container_type="desktop")

            # If successful and we have a desktop container, update it too
            if result and desktop_container:
                # Increment renew count
                desktop_container.renew_count += 1
                db.session.commit()

            return result, message
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error renewing container: {str(e)}")
            traceback.print_exc()
            return False, f'Error renewing container: {str(e)}'

    @staticmethod
    def get_container_status(container_uuid=None, user_id=None):
        """
        Get the status of a container

        Args:
            container_uuid (str, optional): The container UUID
            user_id (int, optional): The user ID

        Returns:
            str: The container status ('running', 'starting', 'stopped', 'expired', or 'expired_renewable')
        """
        if user_id is None and container_uuid is None:
            current_app.logger.error("[Web Desktop] No user_id or container_uuid provided to get_container_status")
            return 'unknown'

        try:
            # Try to determine status from the whale container
            whale_container = None

            # If user_id is provided, use it to find the container
            if user_id:
                whale_container = WhaleContainer.query.filter_by(user_id=user_id, container_type="desktop").first()
            # If container_uuid is provided, use it to find the container
            elif container_uuid:
                whale_container = WhaleContainer.query.filter_by(uuid=container_uuid).first()

            # If no container found, return stopped
            if not whale_container:
                return 'stopped'

            # Check if the container is expired
            timeout = int(get_config("whale:docker_timeout", "3600"))
            if (datetime.datetime.now() - whale_container.start_time).total_seconds() > timeout:
                # Container is expired
                max_renew_count = int(get_config("whale:docker_max_renew_count", "5"))
                if whale_container.renew_count >= max_renew_count:
                    return 'expired'
                return 'expired_renewable'

            # Check container existence using docker API
            try:
                # Check service status by accessing the Docker API directly
                docker_api_url = get_config("whale:docker_api_url", "unix:///var/run/docker.sock")
                client = docker.DockerClient(base_url=docker_api_url)

                # Search for services with the whale_id label
                whale_id = f"{whale_container.user_id}-{whale_container.uuid}"
                services = client.services.list(filters={'label': f'whale_id={whale_id}'})

                if not services:
                    return 'stopped'

                # Check if the service is running properly
                service = services[0]
                tasks = service.tasks()

                # Check if there are any running tasks
                running_tasks = [t for t in tasks if t['Status']['State'] == 'running']

                if running_tasks:
                    return 'running'
                elif any(t['Status']['State'] == 'pending' for t in tasks):
                    return 'starting'
                else:
                    return 'stopped'

            except Exception as e:
                current_app.logger.error(f"[Web Desktop] Error checking Docker service status: {str(e)}")

                # Fallback: Simply check if the container exists in database
                # If it exists, assume it's running (best effort)
                if whale_container:
                    # Get the time since container creation
                    time_since_creation = (datetime.datetime.now() - whale_container.start_time).total_seconds()

                    # Check if the container was recently created (within last 60 seconds)
                    if time_since_creation < 60:
                        current_app.logger.info(f"[Web Desktop] Container is starting (created {time_since_creation:.1f} seconds ago)")
                        return 'starting'
                    else:
                        current_app.logger.info(f"[Web Desktop] Container assumed running (created {time_since_creation:.1f} seconds ago)")
                        return 'running'
                else:
                    return 'stopped'

        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error determining container status: {str(e)}")
            return 'unknown'
