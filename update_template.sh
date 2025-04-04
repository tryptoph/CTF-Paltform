#!/bin/bash
# Save as docker_update_template.sh and make executable

# Execute SQL commands inside the MySQL container
docker-compose exec mysql mysql -u ctfd -pctfd ctfd <<EOF
UPDATE whale_redirect_template 
SET 
    access_template = 'http://localhost:{{ container.port }}',
    frp_template = '[http_{{ container.user_id|string }}-{{ container.uuid }}]
type = tcp
local_ip = {{ container.user_id|string }}-{{ container.uuid }}
local_port = {{ container.challenge.redirect_port }}
remote_port = {{ container.port }}
use_compression = true'
WHERE key = 'http';

UPDATE whale_config
SET value = ''
WHERE key = 'frp_http_domain_suffix';

UPDATE whale_config
SET value = 'true'
WHERE key = 'refresh';
EOF

# Restart CTFd to apply changes
docker-compose restart ctfd

echo "Database updated and CTFd restarted."