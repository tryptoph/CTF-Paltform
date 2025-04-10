from datetime import datetime
from flask import request, abort, session
from flask_restx import Namespace, Resource
from werkzeug.exceptions import Forbidden, NotFound
from flask import current_app

from CTFd.utils import user as current_user
from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import admins_only, authed_only

from .models import WebShellImage, WebShellContainer, db
from .utils.whale_control import ControlUtil

# API namespaces - match CTFd-whale's approach
admin_namespace = Namespace("webshell-admin")
user_namespace = Namespace("webshell-user")


@admin_namespace.errorhandler(NotFound)
@user_namespace.errorhandler(NotFound)
def handle_notfound(err):
    data = {
        'success': False,
        'message': err.description
    }
    return data, 404


@admin_namespace.errorhandler(Forbidden)
@user_namespace.errorhandler(Forbidden)
def handle_forbidden(err):
    message = err.description if 'You don\'t have the permission' not in err.description else 'Please login first'
    data = {
        'success': False,
        'message': message
    }
    return data, 403


@admin_namespace.errorhandler
@user_namespace.errorhandler
def handle_default(err):
    data = {
        'success': False,
        'message': 'Unexpected error occurred'
    }
    return data, 500


@admin_namespace.route('/containers')
class AdminContainers(Resource):
    @staticmethod
    @admins_only
    def get():
        """Get all active WebShell containers"""
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
                        'username': c.user.name,
                        'image_id': c.image_id,
                        'image_name': c.image.name,
                        'start_time': c.start_time.isoformat(),
                        'renew_count': c.renew_count,
                        'status': c.status,
                        'shell_port': c.shell_port,
                        'desktop_port': c.desktop_port,
                        'expired': c.is_expired()
                    } for c in containers
                ],
                'total': count,
                'pages': (count // results_per_page) + (1 if count % results_per_page > 0 else 0),
                'page': page
            }
        }
    
    @staticmethod
    @admins_only
    def patch():
        """Renew a specific container"""
        user_id = request.args.get('user_id', -1)
        result, message = ControlUtil.try_renew_container(user_id=int(user_id))
        if not result:
            abort(403, message)
        return {'success': True, 'message': message}
    
    @staticmethod
    @admins_only
    def delete():
        """Remove a specific container"""
        user_id = request.args.get('user_id')
        if not user_id:
            return {'success': False, 'message': 'User ID is required'}, 400
            
        result, message = ControlUtil.try_remove_container(user_id)
        if not result:
            abort(403, message)
        return {'success': True, 'message': message}


@admin_namespace.route('/images')
class AdminImages(Resource):
    @staticmethod
    @admins_only
    def get():
        """Get all WebShell images"""
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

    @staticmethod
    @admins_only
    def post():
        """Create a new WebShell image"""
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('docker_image'):
            return {'success': False, 'message': 'Name and Docker image are required'}, 400
            
        image = WebShellImage(
            name=data.get('name'),
            docker_image=data.get('docker_image'),
            description=data.get('description', ''),
            memory_limit=data.get('memory_limit', '256m'),
            cpu_limit=float(data.get('cpu_limit', 0.5)),
            timeout=int(data.get('timeout', 3600)),
            port=int(data.get('port', 22)),
            has_desktop=bool(data.get('has_desktop', False)),
            desktop_port=int(data.get('desktop_port', 5900)),
            active=bool(data.get('active', True))
        )
        
        db.session.add(image)
        db.session.commit()
        
        return {'success': True, 'message': 'Image created successfully', 'id': image.id}


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
                current_app.logger.info("[WebShell] No user ID in session")
                return {
                    'success': False, 
                    'message': 'Please login first'
                }, 403
            
            try:
                # Get user's active container
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
                
                # Build response with all necessary info
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
    @authed_only
    def post():
        """Create a new container for the user"""
        current_app.logger.info("[WebShell] POST request to create container")
        
        # Get user details
        user_id = current_user.get_current_user().id
        current_app.logger.info(f"[WebShell] User ID: {user_id}")
        
        # Check if user already has a container
        existing = WebShellContainer.query.filter_by(user_id=user_id).first()
        if existing:
            current_app.logger.warning(f"[WebShell] User {user_id} already has an active container")
            return {'success': False, 'message': 'You already have an active WebShell'}, 400
        
        # Get the image ID from request
        data = request.get_json()
        current_app.logger.info(f"[WebShell] Request data: {data}")
        
        if not data or 'image_id' not in data:
            current_app.logger.warning("[WebShell] Missing image_id in request")
            return {'success': False, 'message': 'Image ID is required'}, 400
            
        image_id = data['image_id']
        current_app.logger.info(f"[WebShell] Image ID: {image_id}")
        
        # Validate the image
        image = WebShellImage.query.filter_by(id=image_id, active=True).first()
        if not image:
            current_app.logger.warning(f"[WebShell] Invalid or inactive image: {image_id}")
            return {'success': False, 'message': 'Invalid or inactive image'}, 400
        
        # Check max container count
        current_count = WebShellContainer.query.count()
        max_containers = int(get_config("webshell:max_container_count", 100))
        if current_count >= max_containers:
            current_app.logger.warning(f"[WebShell] Maximum container limit reached: {current_count}/{max_containers}")
            return {'success': False, 'message': 'Maximum container limit reached'}, 400
        
        # Create and launch container
        current_app.logger.info(f"[WebShell] Creating container for user {user_id} with image {image_id}")
        try:
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
                    'shell_port': container.shell_port,
                    'desktop_port': container.desktop_port,
                    'password': container.password,
                    'access_url': container.access_url,
                    'desktop_url': container.desktop_url
                }
            }
        except Exception as e:
            current_app.logger.exception(f"[WebShell] Exception during container creation: {str(e)}")
            return {'success': False, 'message': f'Error creating container: {str(e)}'}, 500

    @staticmethod
    @authed_only
    def patch():
        """Renew a container"""
        user_id = current_user.get_current_user().id
        current_app.logger.info(f"[WebShell] Renewing container for user {user_id}")
        
        container = WebShellContainer.query.filter_by(user_id=user_id).first()
        
        if not container:
            current_app.logger.warning(f"[WebShell] No active container found for user {user_id}")
            return {'success': False, 'message': 'No active WebShell found'}, 404
        
        # Check renewal count limit
        max_renew = int(get_config("webshell:max_renew_count", 5))
        if container.renew_count >= max_renew:
            current_app.logger.warning(f"[WebShell] Maximum renewal count reached for user {user_id}: {container.renew_count}/{max_renew}")
            return {'success': False, 'message': f'Maximum renewal count ({max_renew}) reached'}, 400
        
        # Renew container
        result, message = ControlUtil.try_renew_container(user_id)
        if not result:
            current_app.logger.error(f"[WebShell] Failed to renew container: {message}")
            return {'success': False, 'message': message}, 400
            
        current_app.logger.info(f"[WebShell] Container renewed successfully for user {user_id}")
        return {'success': True, 'message': 'Container renewed successfully'}

    @staticmethod
    @authed_only
    def delete():
        """Remove user's container"""
        user_id = current_user.get_current_user().id
        current_app.logger.info(f"[WebShell] Removing container for user {user_id}")
        
        result, message = ControlUtil.try_remove_container(user_id)
        
        if not result:
            current_app.logger.error(f"[WebShell] Failed to remove container: {message}")
            return {'success': False, 'message': message}, 400
            
        current_app.logger.info(f"[WebShell] Container removed successfully for user {user_id}")
        return {'success': True, 'message': 'Container removed successfully'}
