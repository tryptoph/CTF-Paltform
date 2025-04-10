from datetime import datetime
from flask import request, abort, session, current_app, jsonify
from flask_restx import Namespace, Resource
from werkzeug.exceptions import Forbidden, NotFound, InternalServerError

from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import admins_only, authed_only

from .models import WebShellImage, WebShellContainer, db
from .utils.whale_control import ControlUtil

# API namespaces - match CTFd-whale's approach
admin_namespace = Namespace("webshell-admin")
user_namespace = Namespace("webshell-user")


# Error handlers
@admin_namespace.errorhandler(NotFound)
@user_namespace.errorhandler(NotFound)
def handle_notfound(err):
    data = {
        'success': False,
        'message': str(err.description)
    }
    return data, 404


@admin_namespace.errorhandler(Forbidden)
@user_namespace.errorhandler(Forbidden)
def handle_forbidden(err):
    message = str(err.description) if 'You don\'t have the permission' not in str(err.description) else 'Please login first'
    data = {
        'success': False,
        'message': message
    }
    return data, 403


@admin_namespace.errorhandler(InternalServerError)
@user_namespace.errorhandler(InternalServerError)
def handle_server_error(err):
    current_app.logger.exception(f"[WebShell] Internal server error: {str(err)}")
    data = {
        'success': False,
        'message': 'Internal server error occurred'
    }
    return data, 500


@admin_namespace.errorhandler
@user_namespace.errorhandler
def handle_default(err):
    current_app.logger.exception(f"[WebShell] Unhandled exception: {str(err)}")
    data = {
        'success': False,
        'message': f'Unexpected error: {str(err)}'
    }
    return data, 500


# Admin API
@admin_namespace.route('/containers')
class AdminContainers(Resource):
    @staticmethod
    @admins_only
    def get():
        """Get all active WebShell containers"""
        try:
            page = abs(request.args.get("page", 1, type=int))
            results_per_page = abs(request.args.get("per_page", 20, type=int))
            page_start = results_per_page * (page - 1)
            
            # Get containers with pagination
            query = WebShellContainer.query.order_by(WebShellContainer.start_time.desc())
            count = query.count()
            containers = query.slice(page_start, page_start + results_per_page).all()
            
            return {
                'success': True,
                'data': {
                    'containers': [
                        {
                            'id': c.id,
                            'user_id': c.user_id,
                            'username': c.user.name if c.user else f"User #{c.user_id}",
                            'image_id': c.image_id,
                            'image_name': c.image.name if c.image else "Unknown",
                            'start_time': c.start_time.isoformat(),
                            'renew_count': c.renew_count,
                            'status': c.status,
                            'desktop_port': c.desktop_port,
                            'expired': c.is_expired()
                        } for c in containers
                    ],
                    'total': count,
                    'pages': (count // results_per_page) + (1 if count % results_per_page > 0 else 0),
                    'page': page
                }
            }
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Error in admin container list: {str(e)}")
            return {'success': False, 'message': f'Error listing containers: {str(e)}'}, 500
    
    @staticmethod
    @admins_only
    def delete():
        """Remove a specific container"""
        try:
            user_id = request.args.get('user_id')
            if not user_id:
                return {'success': False, 'message': 'User ID is required'}, 400
                
            result, message = ControlUtil.try_remove_container(user_id)
            status_code = 200 if result else 400
            return {'success': result, 'message': message}, status_code
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Error in admin container delete: {str(e)}")
            return {'success': False, 'message': f'Error removing container: {str(e)}'}, 500


@admin_namespace.route('/images')
class AdminImages(Resource):
    @staticmethod
    @admins_only
    def get():
        """Get all WebShell images"""
        try:
            images = WebShellImage.query.all()
            return {
                'success': True,
                'data': [
                    {
                        'id': image.id,
                        'name': image.name,
                        'description': image.description,
                        'docker_image': image.docker_image,
                        'memory_limit': image.memory_limit,
                        'cpu_limit': image.cpu_limit,
                        'timeout': image.timeout,
                        'port': image.port,
                        'has_desktop': image.has_desktop,
                        'desktop_port': image.desktop_port,
                        'active': image.active
                    } for image in images
                ]
            }
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Error in admin image list: {str(e)}")
            return {'success': False, 'message': f'Error listing images: {str(e)}'}, 500


# User API
@user_namespace.route('/container')
class UserContainer(Resource):
    @staticmethod
    def get():
        """Get user's active container if any"""
        try:
            # Get user_id directly from session
            user_id = session.get('id')
            current_app.logger.info(f"[WebShell] Getting container for user {user_id}")
            
            # If no user_id in session, return error
            if not user_id:
                current_app.logger.warning("[WebShell] No user ID in session")
                return {
                    'success': False, 
                    'message': 'Please login first'
                }, 403
            
            try:
                # Get the container
                container = WebShellContainer.query.filter_by(user_id=user_id).first()
                
                if not container:
                    current_app.logger.info(f"[WebShell] No container found for user {user_id}")
                    return {'success': True, 'data': None}
                    
                # Check if container is expired
                if container.is_expired():
                    current_app.logger.info(f"[WebShell] Container {container.id} has expired")
                    return {'success': False, 'message': 'Container has expired'}, 400
                
                # Calculate remaining time
                try:
                    remaining_time = container.image.timeout - int((datetime.utcnow() - container.start_time).total_seconds())
                except:
                    remaining_time = 3600  # Default to 1 hour if calculation fails
                    
                current_app.logger.info(f"[WebShell] Returning container info for container {container.id}")
                
                # Build API response safely
                return {
                    'success': True,
                    'data': {
                        'id': container.id,
                        'image_id': container.image_id,
                        'image_name': container.image.name if container.image else 'Unknown',
                        'desktop_port': container.desktop_port,
                        'desktop_url': container.desktop_url,
                        'password': container.password,
                        'start_time': container.start_time.isoformat(),
                        'timeout': container.image.timeout if container.image else 3600,
                        'remaining_time': remaining_time,
                        'renew_count': container.renew_count,
                        'max_renew_count': int(get_config("whale:docker_max_renew_count", 5))
                    }
                }
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Database error getting container: {str(e)}")
                return {'success': False, 'message': f'Error retrieving container data: {str(e)}'}, 500
                
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Unhandled exception in GET /container: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}, 500

    @staticmethod
    def post():
        """Create a new container for the user"""
        try:
            current_app.logger.info("[WebShell] POST request to create container")
            
            # Get user ID from session
            user_id = session.get('id')
            if not user_id:
                current_app.logger.warning("[WebShell] No user ID in session for POST request")
                return {'success': False, 'message': 'Please login first'}, 403
                
            current_app.logger.info(f"[WebShell] User ID: {user_id}")
            
            # Check if user already has a container
            try:
                existing = WebShellContainer.query.filter_by(user_id=user_id).first()
                if existing:
                    current_app.logger.warning(f"[WebShell] User {user_id} already has an active container")
                    return {'success': False, 'message': 'You already have an active WebShell'}, 400
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Error checking for existing container: {str(e)}")
                return {'success': False, 'message': f'Error checking for existing container: {str(e)}'}, 500
            
            # Get the image ID from request
            try:
                data = request.get_json()
                current_app.logger.info(f"[WebShell] Request data: {data}")
                
                if not data:
                    current_app.logger.warning("[WebShell] No JSON data in request")
                    return {'success': False, 'message': 'No data provided'}, 400
                    
                if 'image_id' not in data:
                    current_app.logger.warning("[WebShell] No image_id in request data")
                    return {'success': False, 'message': 'Image ID is required'}, 400
                    
                image_id = data['image_id']
                current_app.logger.info(f"[WebShell] Image ID: {image_id}")
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Error parsing request data: {str(e)}")
                return {'success': False, 'message': f'Error parsing request: {str(e)}'}, 400
            
            # Validate the image
            try:
                image = WebShellImage.query.filter_by(id=image_id, active=True).first()
                if not image:
                    current_app.logger.warning(f"[WebShell] Invalid or inactive image: {image_id}")
                    return {'success': False, 'message': 'Invalid or inactive image'}, 400
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Error validating image: {str(e)}")
                return {'success': False, 'message': f'Error validating image: {str(e)}'}, 500
            
            # Check max container count
            try:
                current_count = WebShellContainer.query.count()
                max_containers = int(get_config("whale:docker_max_container_count", 100))
                if current_count >= max_containers:
                    current_app.logger.warning(f"[WebShell] Maximum container limit reached: {current_count}/{max_containers}")
                    return {'success': False, 'message': 'Maximum container limit reached'}, 400
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Error checking container limits: {str(e)}")
                return {'success': False, 'message': f'Error checking limits: {str(e)}'}, 500
            
            # Create and launch container
            try:
                current_app.logger.info(f"[WebShell] Creating container for user {user_id} with image {image_id}")
                result, message, container = ControlUtil.try_add_container(user_id, image_id)
                
                if not result:
                    current_app.logger.error(f"[WebShell] Failed to create container: {message}")
                    return {'success': False, 'message': message}, 400
                    
                current_app.logger.info(f"[WebShell] Container created successfully: {container.id}")
                return {
                    'success': True,
                    'message': 'Container created successfully',
                    'data': {
                        'id': container.id,
                        'desktop_port': container.desktop_port,
                        'password': container.password,
                        'desktop_url': container.desktop_url
                    }
                }
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Exception during container creation: {str(e)}")
                return {'success': False, 'message': f'Error creating container: {str(e)}'}, 500
                
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Unhandled exception in POST /container: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}, 500

    @staticmethod
    def patch():
        """Renew a container"""
        try:
            current_app.logger.info("[WebShell] PATCH request to renew container")
            
            # Get user ID from session
            user_id = session.get('id')
            if not user_id:
                current_app.logger.warning("[WebShell] No user ID in session for PATCH request")
                return {'success': False, 'message': 'Please login first'}, 403
            
            try:
                container = WebShellContainer.query.filter_by(user_id=user_id).first()
                if not container:
                    current_app.logger.warning(f"[WebShell] No container found for user {user_id}")
                    return {'success': False, 'message': 'No active WebShell found'}, 404
                
                # Check renewal count limit
                max_renew = int(get_config("whale:docker_max_renew_count", 5))
                if container.renew_count >= max_renew:
                    current_app.logger.warning(f"[WebShell] Maximum renewal count reached: {container.renew_count}/{max_renew}")
                    return {'success': False, 'message': f'Maximum renewal count ({max_renew}) reached'}, 400
                
                # Renew container
                result, message = ControlUtil.try_renew_container(user_id)
                if not result:
                    current_app.logger.error(f"[WebShell] Failed to renew container: {message}")
                    return {'success': False, 'message': message}, 400
                    
                current_app.logger.info(f"[WebShell] Container renewed successfully for user {user_id}")
                return {'success': True, 'message': 'Container renewed successfully'}
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Error renewing container: {str(e)}")
                return {'success': False, 'message': f'Error renewing container: {str(e)}'}, 500
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Unhandled exception in PATCH /container: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}, 500

    @staticmethod
    def delete():
        """Remove user's container"""
        try:
            current_app.logger.info("[WebShell] DELETE request to remove container")
            
            # Get user ID from session
            user_id = session.get('id')
            if not user_id:
                current_app.logger.warning("[WebShell] No user ID in session for DELETE request")
                return {'success': False, 'message': 'Please login first'}, 403
                
            try:
                # Check if container exists
                container = WebShellContainer.query.filter_by(user_id=user_id).first()
                if not container:
                    current_app.logger.warning(f"[WebShell] No container found for user {user_id}")
                    return {'success': False, 'message': 'No active WebShell found'}, 404
                
                # Remove container
                result, message = ControlUtil.try_remove_container(user_id)
                if not result:
                    current_app.logger.error(f"[WebShell] Failed to remove container: {message}")
                    return {'success': False, 'message': message}, 400
                    
                current_app.logger.info(f"[WebShell] Container removed successfully for user {user_id}")
                return {'success': True, 'message': 'Container removed successfully'}
            except Exception as e:
                current_app.logger.exception(f"[WebShell] Error removing container: {str(e)}")
                return {'success': False, 'message': f'Error removing container: {str(e)}'}, 500
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Unhandled exception in DELETE /container: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}, 500
