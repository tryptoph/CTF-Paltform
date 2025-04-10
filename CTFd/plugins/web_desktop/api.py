from flask import request, current_app, session
from flask_restx import Namespace, Resource
import importlib

from CTFd.utils.decorators import authed_only, admins_only
from CTFd.utils import get_config, user as current_user
from CTFd.models import db
from CTFd.plugins import bypass_csrf_protection

# Import whale plugin components using importlib to avoid syntax issues with hyphens
try:
    # Import models
    whale_models = importlib.import_module('CTFd.plugins.ctfd-whale.models')
    WhaleContainer = whale_models.WhaleContainer
    DynamicDockerChallenge = whale_models.DynamicDockerChallenge

    # Import control utilities
    whale_control = importlib.import_module('CTFd.plugins.ctfd-whale.utils.control')
    ControlUtil = whale_control.ControlUtil
except Exception as e:
    current_app.logger.error(f"[Web Desktop] Error importing CTFd-whale components: {str(e)}")
    WhaleContainer = None
    DynamicDockerChallenge = None
    ControlUtil = None

from .models import DesktopTemplate
from .utils.control import ControlUtil as DesktopControlUtil

desktop_namespace = Namespace("webdesktop", description="Web Desktop API endpoints")

@desktop_namespace.route('/templates')
class TemplateList(Resource):
    @authed_only
    def get(self):
        """Get all available templates"""
        templates = DesktopTemplate.query.filter_by(is_enabled=True).order_by(
            DesktopTemplate.display_order, DesktopTemplate.id
        ).all()

        result = []
        for template in templates:
            result.append({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'docker_image': template.docker_image,
                'memory_limit': template.memory_limit,
                'cpu_limit': template.cpu_limit,
                'desktop_port': template.desktop_port,
                'icon': template.icon,
                'recommended': template.recommended
            })

        return {"success": True, "data": result}

@desktop_namespace.route('/launch/<int:template_id>')
class LaunchDesktop(Resource):
    @bypass_csrf_protection
    def post(self, template_id):
        """Launch a desktop based on template"""
        if not WhaleContainer or not DynamicDockerChallenge:
            return {"success": False, "message": "Whale plugin components not available"}, 500

        try:
            # Get current user
            user = current_user.get_current_user()
            if not user:
                return {"success": False, "message": "User not found"}, 404

            # Get template
            template = DesktopTemplate.query.filter_by(id=template_id, is_enabled=True).first()
            if not template:
                return {"success": False, "message": "Template not found or not enabled"}, 404

            # Use our own DesktopControlUtil to launch the container
            result, message = DesktopControlUtil.try_add_container(
                user_id=user.id,
                template_id=template_id
            )

            if not result:
                return {"success": False, "message": f"Failed to launch container: {message}"}, 500

            return {"success": True, "message": "Desktop environment is launching"}

        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error launching container: {str(e)}")
            return {"success": False, "message": f"Error launching desktop: {str(e)}"}, 500

@desktop_namespace.route('/container/status')
class ContainerStatus(Resource):
    @authed_only
    def get(self):
        """Get status of current container"""
        if not WhaleContainer:
            return {"success": False, "message": "Whale plugin components not available"}, 500

        try:
            # Get current user
            user = current_user.get_current_user()
            if not user:
                return {"success": False, "message": "User not found"}, 404

            # Get container
            container = WhaleContainer.query.filter_by(user_id=user.id).first()
            if not container:
                return {"success": True, "container": None}

            # Get protocol from config
            https_required = get_config("web_desktop:https_required", "true") == "true"
            protocol = "https" if https_required else "http"

            # Get domain from config
            domain = get_config("web_desktop:domain", "localhost")

            # Calculate expiration time
            import datetime
            timeout = int(get_config("web_desktop:docker_timeout", "3600"))
            expire_date = container.start_time + datetime.timedelta(seconds=timeout)

            # Get container status
            status = DesktopControlUtil.get_container_status(user_id=user.id)

            # Build the response
            return {
                "success": True,
                "container": {
                    "id": container.id,
                    "challenge_id": container.challenge_id,
                    "challenge_name": container.challenge.name if hasattr(container, "challenge") else "Unknown",
                    "start_time": container.start_time.isoformat() if container.start_time else None,
                    "expire_date": expire_date.isoformat(),
                    "renew_count": container.renew_count,
                    "status": status,
                    "port": container.port,
                    "access_url": f"{protocol}://{domain}:{container.port}"
                }
            }

        except Exception as e:
            return {"success": False, "message": f"Error getting container status: {str(e)}"}, 500

@desktop_namespace.route('/admin/templates')
class AdminTemplateList(Resource):
    @admins_only
    @bypass_csrf_protection
    def get(self):
        """Get all templates (admin view)"""
        templates = DesktopTemplate.query.all()

        result = []
        for template in templates:
            result.append({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'docker_image': template.docker_image,
                'memory_limit': template.memory_limit,
                'cpu_limit': template.cpu_limit,
                'desktop_port': template.desktop_port,
                'is_enabled': template.is_enabled,
                'icon': template.icon,
                'display_order': template.display_order,
                'connection_type': template.connection_type,
                'recommended': template.recommended
            })

        return {"success": True, "data": result}

    @admins_only
    @bypass_csrf_protection
    def post(self):
        """Create a new template (admin)"""
        data = request.get_json()

        # Validate required fields
        if not data.get('name') or not data.get('docker_image'):
            return {"success": False, "message": "Name and Docker image are required"}, 400

        # Create the template
        template = DesktopTemplate(
            name=data.get('name'),
            description=data.get('description', ''),
            docker_image=data.get('docker_image'),
            memory_limit=data.get('memory_limit', '2048m'),
            cpu_limit=float(data.get('cpu_limit', 2.0)),
            desktop_port=int(data.get('desktop_port', 6901)),
            is_enabled=bool(data.get('is_enabled', True)),
            icon=data.get('icon', 'kali-logo.svg'),
            display_order=int(data.get('display_order', 0)),
            connection_type=data.get('connection_type', 'direct'),
            recommended=bool(data.get('recommended', False))
        )

        db.session.add(template)
        db.session.commit()

        return {
            "success": True,
            "data": {
                "id": template.id,
                "name": template.name
            }
        }

@desktop_namespace.route('/renew')
class RenewDesktop(Resource):
    @authed_only
    @bypass_csrf_protection
    def post(self):
        """Renew a desktop container"""
        try:
            # Get current user
            user = current_user.get_current_user()
            if not user:
                return {"success": False, "message": "User not found"}, 404

            # Use the desktop control util to renew the container
            result, message = DesktopControlUtil.try_renew_container(user.id)

            if not result:
                return {"success": False, "message": message}, 400

            return {"success": True, "message": "Desktop renewed successfully"}
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error renewing container: {str(e)}")
            return {"success": False, "message": f"Error renewing desktop: {str(e)}"}, 500

@desktop_namespace.route('/destroy')
class DestroyDesktop(Resource):
    @authed_only
    @bypass_csrf_protection
    def post(self):
        """Destroy a desktop container"""
        try:
            # Get current user
            user = current_user.get_current_user()
            if not user:
                return {"success": False, "message": "User not found"}, 404

            # Use the desktop control util to remove the container
            result, message = DesktopControlUtil.try_remove_container(user.id)

            if not result:
                return {"success": False, "message": message}, 400

            return {"success": True, "message": "Desktop destroyed successfully"}
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error destroying container: {str(e)}")
            return {"success": False, "message": f"Error destroying desktop: {str(e)}"}, 500

@desktop_namespace.route('/admin/template/<int:template_id>')
class AdminTemplate(Resource):
    @admins_only
    @bypass_csrf_protection
    def get(self, template_id):
        """Get a template (admin view)"""
        template = DesktopTemplate.query.filter_by(id=template_id).first()
        if not template:
            return {"success": False, "message": "Template not found"}, 404

        return {
            "success": True,
            "data": {
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'docker_image': template.docker_image,
                'memory_limit': template.memory_limit,
                'cpu_limit': template.cpu_limit,
                'desktop_port': template.desktop_port,
                'is_enabled': template.is_enabled,
                'icon': template.icon,
                'display_order': template.display_order,
                'connection_type': template.connection_type,
                'recommended': template.recommended
            }
        }

    @admins_only
    @bypass_csrf_protection
    def put(self, template_id):
        """Update a template (admin)"""
        # Log authentication info for debugging
        current_app.logger.info(f"[Web Desktop] Template update request headers: {dict(request.headers)}")
        current_app.logger.info(f"[Web Desktop] Template update request session: {dict(session)}")

        template = DesktopTemplate.query.filter_by(id=template_id).first()
        if not template:
            return {"success": False, "message": "Template not found"}, 404

        data = request.get_json()

        # Update fields if provided
        if 'name' in data and data['name']:
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if 'docker_image' in data and data['docker_image']:
            template.docker_image = data['docker_image']
        if 'memory_limit' in data and data['memory_limit']:
            template.memory_limit = data['memory_limit']
        if 'cpu_limit' in data:
            try:
                template.cpu_limit = float(data['cpu_limit'])
            except (ValueError, TypeError):
                pass
        if 'desktop_port' in data:
            try:
                template.desktop_port = int(data['desktop_port'])
            except (ValueError, TypeError):
                pass
        if 'is_enabled' in data:
            template.is_enabled = bool(data['is_enabled'])
        if 'icon' in data:
            template.icon = data['icon']
        if 'display_order' in data:
            try:
                template.display_order = int(data['display_order'])
            except (ValueError, TypeError):
                pass
        if 'connection_type' in data:
            template.connection_type = data['connection_type']
        if 'recommended' in data:
            template.recommended = bool(data['recommended'])

        db.session.commit()

        return {"success": True, "message": "Template updated successfully"}

    @admins_only
    @bypass_csrf_protection
    def delete(self, template_id):
        """Delete a template (admin)"""
        template = DesktopTemplate.query.filter_by(id=template_id).first()
        if not template:
            return {"success": False, "message": "Template not found"}, 404

        # Delete the template
        db.session.delete(template)
        db.session.commit()

        return {"success": True, "message": "Template deleted successfully"}


@desktop_namespace.route('/admin/container/<int:container_id>')
class AdminContainer(Resource):
    @admins_only
    @bypass_csrf_protection
    def get(self, container_id):
        """Get a container (admin view)"""
        if not WhaleContainer:
            return {"success": False, "message": "Whale plugin components not available"}, 500

        container = WhaleContainer.query.filter_by(id=container_id).first()
        if not container:
            return {"success": False, "message": "Container not found"}, 404

        return {
            "success": True,
            "data": {
                'id': container.id,
                'user_id': container.user_id,
                'challenge_id': container.challenge_id,
                'start_time': container.start_time.isoformat() if container.start_time else None,
                'renew_count': container.renew_count,
                'port': container.port,
                'status': DesktopControlUtil.get_container_status(container.user_id)
            }
        }

    @admins_only
    @bypass_csrf_protection
    def delete(self, container_id):
        """Destroy a container (admin)"""
        if not WhaleContainer:
            return {"success": False, "message": "Whale plugin components not available"}, 500

        container = WhaleContainer.query.filter_by(id=container_id).first()
        if not container:
            return {"success": False, "message": "Container not found"}, 404

        # Use the desktop control util to remove the container
        result, message = DesktopControlUtil.try_remove_container(container.user_id)

        if not result:
            return {"success": False, "message": message}, 400

        return {"success": True, "message": "Container destroyed successfully"}


@desktop_namespace.route('/admin/container/<int:container_id>/renew')
class AdminContainerRenew(Resource):
    @admins_only
    @bypass_csrf_protection
    def post(self, container_id):
        """Renew a container (admin)"""
        if not WhaleContainer:
            return {"success": False, "message": "Whale plugin components not available"}, 500

        container = WhaleContainer.query.filter_by(id=container_id).first()
        if not container:
            return {"success": False, "message": "Container not found"}, 404

        # Use the desktop control util to renew the container
        result, message = DesktopControlUtil.try_renew_container(container.user_id)

        if not result:
            return {"success": False, "message": message}, 400

        return {"success": True, "message": "Container renewed successfully"}


@desktop_namespace.route('/admin/containers/renew')
class AdminContainersBulkRenew(Resource):
    @admins_only
    @bypass_csrf_protection
    def post(self):
        """Renew multiple containers (admin)"""
        if not WhaleContainer:
            return {"success": False, "message": "Whale plugin components not available"}, 500

        data = request.get_json()
        container_ids = data.get('container_ids', [])

        if not container_ids:
            return {"success": False, "message": "No container IDs provided"}, 400

        results = []
        for container_id in container_ids:
            try:
                container = WhaleContainer.query.filter_by(id=container_id).first()
                if container:
                    result, message = DesktopControlUtil.try_renew_container(container.user_id)
                    results.append({
                        'id': container_id,
                        'success': result,
                        'message': message
                    })
                else:
                    results.append({
                        'id': container_id,
                        'success': False,
                        'message': 'Container not found'
                    })
            except Exception as e:
                results.append({
                    'id': container_id,
                    'success': False,
                    'message': str(e)
                })

        return {
            "success": True,
            "message": "Bulk renew operation completed",
            "results": results
        }


@desktop_namespace.route('/admin/containers/destroy')
class AdminContainersBulkDestroy(Resource):
    @admins_only
    @bypass_csrf_protection
    def post(self):
        """Destroy multiple containers (admin)"""
        if not WhaleContainer:
            return {"success": False, "message": "Whale plugin components not available"}, 500

        data = request.get_json()
        container_ids = data.get('container_ids', [])

        if not container_ids:
            return {"success": False, "message": "No container IDs provided"}, 400

        results = []
        for container_id in container_ids:
            try:
                container = WhaleContainer.query.filter_by(id=container_id).first()
                if container:
                    result, message = DesktopControlUtil.try_remove_container(container.user_id)
                    results.append({
                        'id': container_id,
                        'success': result,
                        'message': message
                    })
                else:
                    results.append({
                        'id': container_id,
                        'success': False,
                        'message': 'Container not found'
                    })
            except Exception as e:
                results.append({
                    'id': container_id,
                    'success': False,
                    'message': str(e)
                })

        return {
            "success": True,
            "message": "Bulk destroy operation completed",
            "results": results
        }
