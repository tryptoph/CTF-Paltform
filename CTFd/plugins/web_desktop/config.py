"""
Configuration settings for the Web Desktop plugin
"""

# Default configuration values
DEFAULT_CONFIG = {
    # Docker settings
    "docker_timeout": 3600,  # 1 hour
    "docker_max_renew_count": 5,
    "docker_dns": "8.8.8.8,8.8.4.4",
    "docker_auto_connect_network": "ctfd_frp-containers",

    # Port range for desktop containers
    "port_start": 10000,
    "port_end": 11000,

    # Domain settings
    "domain": "localhost",
    "https_required": "true",

    # Template settings
    "template_http_subdomain": "{{ container.uuid }}",

    # FRP settings (sync with CTFd-whale)
    "frp_api_ip": "frpc",
    "frp_api_port": "7400",
    "frp_api_url": "",  # If empty, will use frp_api_ip and frp_api_port
    "frp_direct_ip_address": "",
    "frp_direct_port_range": "10000-11000",
    "frp_config_template": ""
}

def get_default_config():
    """
    Get the default configuration values

    Returns:
        dict: The default configuration values
    """
    return DEFAULT_CONFIG.copy()
