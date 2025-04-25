import functools
import importlib
import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, abort, session
from CTFd.utils.security.csrf import generate_nonce

from CTFd.models import db, Challenges
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
    register_user_page_menu_bar
)
from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import authed_only, admins_only
from CTFd.utils.user import get_current_user, is_admin
from CTFd.api import CTFd_API_v1

# Custom admin check for blueprints
def blueprint_admin_only(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if is_admin():
            return f(*args, **kwargs)
        else:
            abort(403)
    return decorated_function

# Import whale plugin components directly - no intermediate "get" methods
try:
    whale_models = importlib.import_module('CTFd.plugins.ctfd-whale.models')
    WhaleContainer = whale_models.WhaleContainer
    DynamicDockerChallenge = whale_models.DynamicDockerChallenge
    WhaleConfig = whale_models.WhaleConfig

    # Log successful import
    print("[Web Desktop] Successfully imported CTFd-whale models")

    # Import control directly, not through methods
    whale_control = importlib.import_module('CTFd.plugins.ctfd-whale.utils.control')
    WhaleControlUtil = whale_control.ControlUtil

    # Import DB container
    whale_db = importlib.import_module('CTFd.plugins.ctfd-whale.utils.db')
    WhaleDBContainer = None
    if hasattr(whale_db, 'DBContainer'):
        WhaleDBContainer = whale_db.DBContainer
except Exception as e:
    current_app.logger.error(f"[Web Desktop] Error importing CTFd-whale components: {str(e)}")
    WhaleContainer = None
    DynamicDockerChallenge = None
    WhaleConfig = None
    WhaleControlUtil = None
    WhaleDBContainer = None

from .models import DesktopTemplate, DesktopConfig, DesktopContainer, ChallengeDesktopLink, create_all
from .utils.migrations import upgrade as db_upgrade
from .api import desktop_namespace

# Custom date filter for templates
def date_filter(value, format='%Y-%m-%d %H:%M:%S'):
    if value:
        return value.strftime(format)
    return ''

# Config wrapper class for templates
class ConfigWrapper:
    def __init__(self, get_config_func):
        self.get_config_func = get_config_func

    def get(self, key, default=None):
        return self.get_config_func(key, default)

def load(app):
    # Add the plugin name to app config
    plugin_name = __name__.split('.')[-1]

    # Register plugin assets
    register_plugin_assets_directory(
        app, base_path=f"/plugins/{plugin_name}/assets",
        endpoint=f'plugins.{plugin_name}.assets'
    )

    # Add date filter to Jinja
    app.jinja_env.filters['date'] = date_filter

    # Create blueprint
    page_blueprint = Blueprint(
        "web_desktop",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/web_desktop"
    )

    # Create database tables and upgrade database
    with app.app_context():
        # Create all tables defined in models.py using our custom function
        try:
            success = create_all()
            if success:
                current_app.logger.info("[Web Desktop] Created database tables")
            else:
                current_app.logger.warning("[Web Desktop] Some tables may not have been created properly")
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error creating database tables: {str(e)}")

        # Run migrations
        try:
            db_upgrade()
            current_app.logger.info("[Web Desktop] Database migrations completed")
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error running database migrations: {str(e)}")

    # Set default configs if not already set
    if not get_config("web_desktop:domain"):
        # Import domain from whale if available
        domain = get_config("whale:domain_hostname", "localhost")
        set_config("web_desktop:domain", domain)

    if not get_config("web_desktop:https_required"):
        set_config("web_desktop:https_required", "true")

    if not get_config("web_desktop:docker_timeout"):
        timeout = get_config("whale:docker_timeout", "3600")
        set_config("web_desktop:docker_timeout", timeout)

    if not get_config("web_desktop:docker_max_renew_count"):
        max_renew = get_config("whale:docker_max_renew_count", "5")
        set_config("web_desktop:docker_max_renew_count", max_renew)

    # Route for desktop view
    @page_blueprint.route('/', methods=['GET'])
    def desktop_view():
        try:
            # Check if user is authenticated
            if not is_admin() and not get_current_user():
                return redirect(url_for('auth.login', next=request.path))

            # Get current user
            user = get_current_user()

            # Get user's container (use whale container directly)
            whale_container = None
            template_info = None
            challenge_container = None

            if WhaleContainer:
                whale_container = WhaleContainer.query.filter_by(user_id=user.id, container_type="desktop").first()

                # Check if user has a challenge container
                if WhaleContainer:
                    challenge_container = WhaleContainer.query.filter_by(user_id=user.id, container_type="challenge").first()

                    # If we have a challenge container, get the internal port from the challenge
                    if challenge_container and challenge_container.challenge_id:
                        # Get the DynamicDockerChallenge to find the internal port
                        if DynamicDockerChallenge:
                            challenge = DynamicDockerChallenge.query.filter_by(id=challenge_container.challenge_id).first()
                            if challenge:
                                # Store the internal port in the container object for template access
                                challenge_container.internal_port = challenge.redirect_port
                                current_app.logger.info(f"[Web Desktop] Challenge internal port: {challenge.redirect_port}")

                # If we have a container, try to get its template info
                if whale_container:
                    # Get the desktop container to find the template_id
                    desktop_container = DesktopContainer.query.filter_by(user_id=user.id).first()
                    if desktop_container and desktop_container.template_id:
                        template_info = DesktopTemplate.query.filter_by(id=desktop_container.template_id).first()
                        current_app.logger.info(f"[Web Desktop] Found template: {template_info.name if template_info else 'None'}, Docker image: {template_info.docker_image if template_info else 'None'}")

            # Get templates
            templates = DesktopTemplate.query.filter_by(is_enabled=True).all()
            current_app.logger.info(f"[Web Desktop] Found {len(templates)} enabled templates")
            for template in templates:
                current_app.logger.info(f"[Web Desktop] Template: {template.name}, Enabled: {template.is_enabled}")

            # Generate nonce for CSRF protection
            nonce = generate_nonce()

            # Store the nonce in the session
            session['nonce'] = nonce
            current_app.logger.debug(f"[Web Desktop] Generated nonce: {nonce}")

            # Create a config wrapper for the template
            config_wrapper = ConfigWrapper(get_config)

            return render_template(
                'desktop.html',
                user=user,
                container=whale_container,
                template_info=template_info,
                templates=templates,
                nonce=nonce,
                now=datetime.datetime.now(),
                config=config_wrapper,
                challenge_container=challenge_container
            )
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error in desktop_view: {str(e)}")
            # Render a more user-friendly error template
            return render_template(
                'error.html',
                error_title="Error Loading Web Desktop",
                error_message="There was a problem loading your desktop environment. Please try again later or contact an administrator.",
                debug_info=str(e) if is_admin() else None  # Only show detailed error to admins
            )

    # Admin panel routes
    @page_blueprint.route('/admin', methods=['GET'])
    @blueprint_admin_only
    def admin_panel():
        try:
            # Get settings directly
            domain = get_config("web_desktop:domain", "localhost")
            https_required = get_config("web_desktop:https_required", "true") == "true"

            # Generate nonce
            nonce = generate_nonce()

            # Store the nonce in the session
            session['nonce'] = nonce

            # Create a config wrapper for the template
            config_wrapper = ConfigWrapper(get_config)

            return render_template(
                'admin_settings.html',
                hostname=domain,
                https_required=https_required,
                nonce=nonce,
                config=config_wrapper
            )
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error in admin_panel: {str(e)}")
            return f"""
            <div class="container p-3">
                <div class="alert alert-danger">
                    <h4>Error Loading Admin Panel</h4>
                    <p>{str(e)}</p>
                    <a href="/admin" class="btn btn-primary">Return to Admin</a>
                </div>
            </div>
            """

    @page_blueprint.route('/admin/templates', methods=['GET'])
    @blueprint_admin_only
    def admin_templates():
        try:
            # Get templates directly from the database
            templates = DesktopTemplate.query.all()

            # Generate nonce
            nonce = generate_nonce()

            # Store the nonce in the session
            session['nonce'] = nonce

            # We'll use the same nonce for CSRF protection
            csrf_nonce = nonce

            # Create a config wrapper for the template
            config_wrapper = ConfigWrapper(get_config)

            return render_template(
                'admin_templates.html',
                templates=templates,
                nonce=nonce,
                csrf_nonce=csrf_nonce,
                config=config_wrapper
            )
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error in admin_templates: {str(e)}")
            return f"""
            <div class="container p-3">
                <div class="alert alert-danger">
                    <h4>Error Loading Templates</h4>
                    <p>{str(e)}</p>
                    <a href="/plugins/web_desktop/admin" class="btn btn-primary">Return to Admin</a>
                </div>
            </div>
            """

    @page_blueprint.route('/admin/containers', methods=['GET'])
    @blueprint_admin_only
    def admin_containers():
        try:
            # Get page parameters
            page = abs(request.args.get("page", 1, type=int))
            results_per_page = 10
            page_start = results_per_page * (page - 1)

            # Get view mode
            view_mode = request.args.get('mode', session.get('view_mode', 'list'))
            session['view_mode'] = view_mode

            # Get containers
            containers = []
            pages = 1
            curr_page = 1

            if WhaleContainer:
                try:
                    # Get desktop containers only
                    query = WhaleContainer.query

                    # Try to filter by container_type if the column exists
                    try:
                        query = query.filter(WhaleContainer.container_type == "desktop")
                    except Exception as filter_error:
                        current_app.logger.warning(f"[Web Desktop] Could not filter by container_type: {str(filter_error)}")

                    # Count and paginate
                    count = query.count()
                    whale_containers = query.order_by(WhaleContainer.id.desc()).slice(page_start, page_start + results_per_page).all()

                    # Process containers for display
                    processed_containers = []
                    for container in whale_containers:
                        # Create a dictionary with container data
                        container_data = {
                            'id': container.id,
                            'user_id': container.user_id,
                            'user': container.user,
                            'start_time': container.start_time,
                            'port': container.port,
                            'uuid': container.uuid,
                            'status': 'Running',  # Default status
                            'template_name': 'Unknown'  # Default template name
                        }

                        # Try to find a matching template
                        try:
                            if container.challenge_id:
                                # Look for a desktop template linked to this challenge
                                link = ChallengeDesktopLink.query.filter_by(challenge_id=container.challenge_id).first()
                                if link and link.template:
                                    container_data['template'] = link.template
                                    container_data['template_name'] = link.template.name
                        except Exception as template_error:
                            current_app.logger.warning(f"[Web Desktop] Error finding template: {str(template_error)}")

                        processed_containers.append(container_data)

                    containers = processed_containers
                    pages = (count // results_per_page) + (1 if count % results_per_page > 0 else 0)
                    curr_page = min(page, pages) if pages > 0 else 1
                except Exception as container_error:
                    current_app.logger.error(f"[Web Desktop] Error processing containers: {str(container_error)}")
                    # Continue with empty containers list

            # Generate nonce
            nonce = generate_nonce()

            # Store the nonce in the session
            session['nonce'] = nonce

            # Create a config wrapper for the template
            config_wrapper = ConfigWrapper(get_config)

            return render_template(
                'admin_containers.html',
                containers=containers,
                pages=pages,
                curr_page=curr_page,
                view_mode=view_mode,
                nonce=nonce,
                config=config_wrapper
            )
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error in admin_containers: {str(e)}")
            return f"""
            <div class="container p-3">
                <div class="alert alert-danger">
                    <h4>Error Loading Containers</h4>
                    <p>{str(e)}</p>
                    <a href="/plugins/web_desktop/admin" class="btn btn-primary">Return to Admin</a>
                </div>
            </div>
            """

    # Add template route
    @page_blueprint.route('/admin/add_template', methods=['POST'])
    @blueprint_admin_only
    def add_template():
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description', '')
            docker_image = request.form.get('docker_image')
            memory_limit = request.form.get('memory_limit', '512m')
            cpu_limit = float(request.form.get('cpu_limit', 2.0))
            desktop_port = int(request.form.get('desktop_port', 6901))
            is_enabled = request.form.get('is_enabled') == 'on'
            icon = request.form.get('icon', 'kali-logo.svg')
            display_order = int(request.form.get('display_order', 0))
            connection_type = request.form.get('connection_type', 'direct')
            recommended = request.form.get('recommended') == 'on'

            # Validate
            if not name or not docker_image:
                flash("Name and Docker image are required", "error")
                return redirect(url_for('web_desktop.admin_panel'))

            # Create template
            template = DesktopTemplate(
                name=name,
                description=description,
                docker_image=docker_image,
                memory_limit=memory_limit,
                cpu_limit=cpu_limit,
                desktop_port=desktop_port,
                is_enabled=is_enabled,  # Make sure this is set correctly
                icon=icon,
                display_order=display_order,
                connection_type=connection_type,
                recommended=recommended
            )

            # Save
            db.session.add(template)
            db.session.commit()

            # Log template creation
            current_app.logger.info(f"[Web Desktop] Template created: {name}, Enabled: {is_enabled}")

            flash("Template added successfully", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"[Web Desktop] Error adding template: {str(e)}")
            flash(f"Error adding template: {str(e)}", "error")

        return redirect(url_for('web_desktop.admin_panel'))

    # Import our own ControlUtil
    from .utils.control import ControlUtil as DesktopControlUtil

    # Launch desktop route
    @page_blueprint.route('/launch/<int:template_id>', methods=['POST'])
    def launch_desktop(template_id):
        try:
            # Check if user is authenticated
            if not is_admin() and not get_current_user():
                return redirect(url_for('auth.login', next=request.path))

            # Verify CSRF token
            if request.method == 'POST':
                submitted_nonce = request.form.get('nonce')
                session_nonce = session.get('nonce')

                # Debug logging
                current_app.logger.info(f"[Web Desktop] Launch - Submitted nonce: {submitted_nonce}")
                current_app.logger.info(f"[Web Desktop] Launch - Session nonce: {session_nonce}")
                current_app.logger.info(f"[Web Desktop] Launch - Session data: {session}")

                # Verify CSRF token
                if not submitted_nonce or submitted_nonce != session_nonce:
                    current_app.logger.warning(f"[Web Desktop] CSRF token mismatch: {submitted_nonce} vs {session_nonce}")
                    flash("Invalid security token. Please try again.", "error")
                    return redirect(url_for('web_desktop.desktop_view'))

            # Get current user
            user = get_current_user()
            if not user:
                flash("User not found", "error")
                return redirect(url_for('web_desktop.desktop_view'))

            # Get template
            template = DesktopTemplate.query.filter_by(id=template_id, is_enabled=True).first()
            if not template:
                flash("Template not found or not enabled", "error")
                return redirect(url_for('web_desktop.desktop_view'))

            # Use our own DesktopControlUtil to launch the container
            if WhaleControlUtil:
                # First, remove any existing container
                try:
                    existing_container = WhaleContainer.query.filter_by(user_id=user.id).first()
                    if existing_container:
                        DesktopControlUtil.try_remove_container(user.id)
                except Exception as e:
                    current_app.logger.error(f"[Web Desktop] Error removing existing container: {str(e)}")

                # Now create the new container
                result, message = DesktopControlUtil.try_add_container(
                    user_id=user.id,
                    template_id=template_id
                )

                if result:
                    flash("Desktop environment is launching. Please wait a moment...", "success")
                else:
                    flash(f"Failed to launch container: {message}", "error")
            else:
                flash("Container management system not available. Please contact an administrator.", "error")

            return redirect(url_for('web_desktop.desktop_view'))
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error launching container: {str(e)}")
            flash(f"Error launching desktop: {str(e)}", "error")
            return redirect(url_for('web_desktop.desktop_view'))

    # Renew desktop route
    @page_blueprint.route('/renew', methods=['POST'])
    def renew_desktop():
        try:
            # Check if user is authenticated
            if not is_admin() and not get_current_user():
                return redirect(url_for('auth.login', next=request.path))

            # Verify CSRF token
            if request.method == 'POST':
                submitted_nonce = request.form.get('nonce')
                session_nonce = session.get('nonce')

                # Debug logging
                current_app.logger.info(f"[Web Desktop] Renew - Submitted nonce: {submitted_nonce}")
                current_app.logger.info(f"[Web Desktop] Renew - Session nonce: {session_nonce}")

                # Verify CSRF token
                if not submitted_nonce or submitted_nonce != session_nonce:
                    current_app.logger.warning(f"[Web Desktop] CSRF token mismatch in renew: {submitted_nonce} vs {session_nonce}")
                    flash("Invalid security token. Please try again.", "error")
                    return redirect(url_for('web_desktop.desktop_view'))

            # Get current user
            user = get_current_user()
            if not user:
                flash("User not found", "error")
                return redirect(url_for('web_desktop.desktop_view'))

            # Use our own DesktopControlUtil to renew the container
            if WhaleControlUtil:
                result, message = DesktopControlUtil.try_renew_container(user.id)

                if result:
                    flash("Desktop time renewed successfully.", "success")
                else:
                    flash(f"Failed to renew container: {message}", "error")
            else:
                flash("Container management system not available. Please contact an administrator.", "error")

            return redirect(url_for('web_desktop.desktop_view'))
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error renewing container: {str(e)}")
            flash(f"Error renewing desktop: {str(e)}", "error")
            return redirect(url_for('web_desktop.desktop_view'))

    # Destroy desktop route
    @page_blueprint.route('/destroy', methods=['POST'])
    def destroy_desktop():
        try:
            # Check if user is authenticated
            if not is_admin() and not get_current_user():
                return redirect(url_for('auth.login', next=request.path))

            # Verify CSRF token
            if request.method == 'POST':
                submitted_nonce = request.form.get('nonce')
                session_nonce = session.get('nonce')

                # Debug logging
                current_app.logger.info(f"[Web Desktop] Destroy - Submitted nonce: {submitted_nonce}")
                current_app.logger.info(f"[Web Desktop] Destroy - Session nonce: {session_nonce}")

                # Verify CSRF token
                if not submitted_nonce or submitted_nonce != session_nonce:
                    current_app.logger.warning(f"[Web Desktop] CSRF token mismatch in destroy: {submitted_nonce} vs {session_nonce}")
                    flash("Invalid security token. Please try again.", "error")
                    return redirect(url_for('web_desktop.desktop_view'))

            # Get current user
            user = get_current_user()
            if not user:
                flash("User not found", "error")
                return redirect(url_for('web_desktop.desktop_view'))

            # Use our own DesktopControlUtil to destroy the container
            if WhaleControlUtil:
                result, message = DesktopControlUtil.try_remove_container(user.id)

                if result:
                    flash("Desktop destroyed successfully.", "success")
                else:
                    flash(f"Failed to destroy container: {message}", "error")
            else:
                flash("Container management system not available. Please contact an administrator.", "error")

            return redirect(url_for('web_desktop.desktop_view'))
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error destroying container: {str(e)}")
            flash(f"Error destroying desktop: {str(e)}", "error")
            return redirect(url_for('web_desktop.desktop_view'))

    # Toggle template enabled/disabled
    @page_blueprint.route('/admin/toggle_template/<int:template_id>', methods=['POST'])
    @blueprint_admin_only
    def toggle_template(template_id):
        try:
            # Get template
            template = DesktopTemplate.query.filter_by(id=template_id).first()
            if not template:
                flash("Template not found", "error")
                return redirect(url_for('web_desktop.admin_panel'))

            # Toggle enabled status
            template.is_enabled = not template.is_enabled
            db.session.commit()

            # Log template status change
            status = "enabled" if template.is_enabled else "disabled"
            current_app.logger.info(f"[Web Desktop] Template {template.name} {status}: ID={template.id}, is_enabled={template.is_enabled}")
            flash(f"Template {template.name} {status} successfully", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"[Web Desktop] Error toggling template: {str(e)}")
            flash(f"Error toggling template: {str(e)}", "error")

        return redirect(url_for('web_desktop.admin_panel'))

    # Settings update route
    @page_blueprint.route('/admin/settings', methods=['POST'])
    @blueprint_admin_only
    def update_settings():
        try:
            # Get form data
            domain = request.form.get('domain', 'localhost')
            https_required = request.form.get('https_required') == 'on'
            docker_timeout = request.form.get('docker_timeout', '3600')
            max_renew_count = request.form.get('docker_max_renew_count', '5')

            # Save settings
            set_config("web_desktop:domain", domain)
            set_config("web_desktop:https_required", "true" if https_required else "false")
            set_config("web_desktop:docker_timeout", docker_timeout)
            set_config("web_desktop:docker_max_renew_count", max_renew_count)

            # Update whale domain if needed
            current_whale_domain = get_config("whale:domain_hostname")
            if current_whale_domain != domain:
                set_config("whale:domain_hostname", domain)
                set_config("whale:refresh", "true")

                # Update direct template if available
                if WhaleConfig:
                    try:
                        # Update the direct template with correct protocol
                        protocol = "https" if https_required else "http"

                        # Get direct template from whale using direct query
                        direct_template = whale_models.WhaleRedirectTemplate.query.filter_by(key='direct').first()

                        if direct_template:
                            direct_template.access_template = f'<div style="text-align: center; margin: 15px 0;"><a href="{protocol}://{domain}:{{{{ container.port }}}}" target="_blank" style="font-size: 16px; font-weight: bold; padding: 8px 16px; background-color: #f8f9fa; border-radius: 4px; text-decoration: none; display: inline-block;">{domain}:{{{{ container.port }}}}</a></div>'

                            # Set refresh flag
                            refresh_config = WhaleConfig.query.filter_by(key='refresh').first()
                            if refresh_config:
                                refresh_config.value = 'true'
                            else:
                                db.session.add(WhaleConfig('refresh', 'true'))

                            db.session.commit()
                    except Exception as e:
                        current_app.logger.error(f"[Web Desktop] Error updating whale templates: {str(e)}")

            flash("Settings updated successfully", "success")
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error updating settings: {str(e)}")
            flash(f"Error updating settings: {str(e)}", "error")

        return redirect(url_for('web_desktop.admin_panel'))

    # Register API namespace
    CTFd_API_v1.add_namespace(desktop_namespace, path="/plugins/webdesktop")

    # Register admin and user menus
    register_admin_plugin_menu_bar(
        "Web Desktop",
        "/plugins/web_desktop/admin"
    )

    register_user_page_menu_bar(
        "Web Desktop",
        "/plugins/web_desktop/"
    )

    # Redirect routes
    @app.route('/desktop', methods=['GET'])
    @authed_only
    def desktop_redirect():
        return redirect(url_for('web_desktop.desktop_view'))

    @app.route('/admin/webdesktop', methods=['GET'])
    @admins_only
    def admin_webdesktop_redirect():
        return redirect(url_for('web_desktop.admin_panel'))

    # Debug route for admins
    @page_blueprint.route('/admin/debug', methods=['GET'])
    @blueprint_admin_only
    def admin_debug():
        try:
            # Get session data
            session_data = dict(session)

            # Create a safe version of the session data
            safe_session = {}
            for key, value in session_data.items():
                if key in ['nonce', 'csrf_nonce', 'user_id', 'admin']:
                    safe_session[key] = value
                else:
                    safe_session[key] = f"<{type(value).__name__}>"

            return render_template(
                'debug.html',
                session_data=safe_session,
                nonce=session.get('nonce', 'Not set'),
                csrf_nonce=session.get('csrf_nonce', 'Not set')
            )
        except Exception as e:
            current_app.logger.error(f"[Web Desktop] Error in admin_debug: {str(e)}")
            return f"""
            <div class="container p-3">
                <div class="alert alert-danger">
                    <h4>Error Loading Debug Info</h4>
                    <p>{str(e)}</p>
                    <a href="/plugins/web_desktop/admin" class="btn btn-primary">Return to Admin</a>
                </div>
            </div>
            """

    # Register blueprint
    app.register_blueprint(page_blueprint)

    return app