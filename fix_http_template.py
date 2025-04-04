import os
import sys

# Add the CTFd directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from CTFd import create_app
from CTFd.plugins.ctfd-whale.models import WhaleRedirectTemplate
from CTFd.utils import set_config, get_config
from CTFd.models import db

app = create_app()

with app.app_context():
    # First, check current templates
    http_template = WhaleRedirectTemplate.query.filter_by(key='http').first()
    
    if http_template:
        print("Current HTTP access template:", http_template.access_template)
        
        # Fix the HTTP access template
        new_access_template = "http://{{ container.uuid }}.{{ get_config('whale:frp_http_domain_suffix', 'localhost') }}"
        http_template.access_template = new_access_template
        
        # Set the domain suffix if not already set
        if not get_config('whale:frp_http_domain_suffix'):
            set_config('whale:frp_http_domain_suffix', 'localhost')
        
        # Save changes
        db.session.commit()
        print("Updated HTTP access template to:", new_access_template)
    else:
        print("HTTP template not found. Creating it...")
        new_http_template = WhaleRedirectTemplate(
            key='http',
            access_template="http://{{ container.uuid }}.{{ get_config('whale:frp_http_domain_suffix', 'localhost') }}",
            frp_template="""
[{{ container.uuid }}]
type = http
local_port = {{ container.challenge.redirect_port }}
subdomain = {{ container.uuid }}
"""
        )
        db.session.add(new_http_template)
        db.session.commit()
        print("Created new HTTP template")

    # For added assurance, let's also check the direct template
    direct_template = WhaleRedirectTemplate.query.filter_by(key='direct').first()
    if direct_template:
        print("Current Direct access template:", direct_template.access_template)

print("Done! Please restart the CTFd server for changes to take effect.")