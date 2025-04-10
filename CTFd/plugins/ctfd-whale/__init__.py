import fcntl

import requests
from flask import Blueprint, render_template, session, current_app, request
from flask_apscheduler import APScheduler

from CTFd.api import CTFd_API_v1
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils.security.csrf import generate_nonce
from CTFd.utils import get_config, set_config
from .api import *
from .challenge_type import DynamicValueDockerChallenge
from .utils.cache import CacheProvider
from .utils.control import ControlUtil
from .utils.db import DBContainer, DBConfig
from .utils.docker import DockerUtils
from .utils.exceptions import WhaleError
from .utils.setup import setup_default_configs
from .models import WhaleRedirectTemplate, WhaleConfig


def load(app):
    # upgrade()
    plugin_name = __name__.split('.')[-1]
    set_config('whale:plugin_name', plugin_name)
    app.db.create_all()
    if not get_config("whale:setup"):
        if not DBConfig.get_config('setup'):
            setup_default_configs()
        else:
            for key, val in DBConfig.get_all_configs().items():
                set_config('whale:' + key, val)

    # Force update the direct template with a properly centered URL
    with app.app_context():
        direct_template = WhaleRedirectTemplate.query.filter_by(key='direct').first()
        if direct_template:
            hostname = get_config('whale:domain_hostname', 'localhost')
            # Check if HTTPS is required from web_desktop plugin
            https_required = get_config('web_desktop:https_required', 'true') == 'true'
            protocol = 'https' if https_required else 'http'
            direct_template.access_template = f'<div style="text-align: center; margin: 15px 0;"><a href="{protocol}://{hostname}:{{{{ container.port }}}}" target="_blank" style="font-size: 16px; font-weight: bold; padding: 8px 16px; background-color: #f8f9fa; border-radius: 4px; text-decoration: none; display: inline-block;">{hostname}:{{{{ container.port }}}}</a></div>'

            # Force refresh flag to ensure changes are applied
            refresh_config = WhaleConfig.query.filter_by(key='refresh').first()
            if refresh_config:
                refresh_config.value = 'true'
            else:
                app.db.session.add(WhaleConfig('refresh', 'true'))

            app.db.session.commit()
            print(f"[CTFd Whale] Updated direct template with centered URL using hostname: {hostname}")

    register_plugin_assets_directory(
        app, base_path=f"/plugins/{plugin_name}/assets",
        endpoint='plugins.ctfd-whale.assets'
    )
    register_admin_plugin_menu_bar(
        title='Whale',
        route='/plugins/ctfd-whale/admin/settings'
    )

    DynamicValueDockerChallenge.templates = {
        "create": f"/plugins/{plugin_name}/assets/create.html",
        "update": f"/plugins/{plugin_name}/assets/update.html",
        "view": f"/plugins/{plugin_name}/assets/view.html",
    }
    DynamicValueDockerChallenge.scripts = {
        "create": "/plugins/ctfd-whale/assets/create.js",
        "update": "/plugins/ctfd-whale/assets/update.js",
        "view": "/plugins/ctfd-whale/assets/view.js",
    }
    CHALLENGE_CLASSES["dynamic_docker"] = DynamicValueDockerChallenge

    page_blueprint = Blueprint(
        "ctfd-whale",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/ctfd-whale"
    )
    CTFd_API_v1.add_namespace(admin_namespace, path="/plugins/ctfd-whale/admin")
    CTFd_API_v1.add_namespace(user_namespace, path="/plugins/ctfd-whale")
    DockerUtils.init()

    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        if get_config("whale:refresh", "false"):
            CacheProvider(app=current_app).init_port_sets()
            set_config("whale:refresh", "false")
        return render_template('whale_config.html')

    @page_blueprint.route("/admin/containers")
    @admins_only
    def admin_list_containers():
        result = AdminContainers.get()
        view_mode = request.args.get('mode', session.get('view_mode', 'list'))
        session['view_mode'] = view_mode
        return render_template("whale_containers.html",
                               plugin_name=plugin_name,
                               containers=result['data']['containers'],
                               pages=result['data']['pages'],
                               curr_page=abs(request.args.get("page", 1, type=int)),
                               curr_page_start=result['data']['page_start'])

    def auto_clean_container():
        with app.app_context():
            results = DBContainer.get_all_expired_container()
            for r in results:
                ControlUtil.try_remove_container(r.user_id)

            containers = DBContainer.get_all_alive_container()

            config = ''.join([c.frp_config for c in containers])

            try:
                # you can authorize a connection by setting
                # frp_url = http://user:pass@ip:port
                frp_addr = get_config("whale:frp_api_url")
                if not frp_addr:
                    frp_addr = f'http://{get_config("whale:frp_api_ip", "frpc")}:{get_config("whale:frp_api_port", "7400")}'
                    # backward compatibility
                common = get_config("whale:frp_config_template", '')
                if '[common]' in common:
                    output = common + config
                else:
                    remote = requests.get(f'{frp_addr.rstrip("/")}/api/config')
                    assert remote.status_code == 200
                    set_config("whale:frp_config_template", remote.text)
                    output = remote.text + config
                assert requests.put(
                    f'{frp_addr.rstrip("/")}/api/config', output, timeout=5
                ).status_code == 200
                assert requests.get(
                    f'{frp_addr.rstrip("/")}/api/reload', timeout=5
                ).status_code == 200
            except (requests.RequestException, AssertionError):
                raise WhaleError(
                    'frpc request failed\n' +
                    'please check the frp related configs'
                )

    app.register_blueprint(page_blueprint)

    try:
        lock_file = open("/tmp/ctfd_whale.lock", "w")
        lock_fd = lock_file.fileno()
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        scheduler.add_job(
            id='whale-auto-clean', func=auto_clean_container,
            trigger="interval", seconds=10
        )

        redis_util = CacheProvider(app=app)
        redis_util.init_port_sets()

        print("[CTFd Whale] Started successfully")
    except IOError:
        pass