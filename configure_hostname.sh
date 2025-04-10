#!/bin/bash
# Script to update the hostname configuration for CTFd-whale plugin

# Check if a hostname argument was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <hostname>"
    echo "Example: $0 myctf.example.com"
    exit 1
fi

# The hostname provided by the user
HOSTNAME=$1

# Path to the main CTFd directory
CTFD_DIR="$(pwd)"

# Check if we're in the right directory
if [ ! -d "$CTFD_DIR/CTFd" ] || [ ! -d "$CTFD_DIR/CTFd/plugins/ctfd-whale" ]; then
    echo "Error: This script must be run from the CTFd root directory"
    exit 1
fi

echo "Setting hostname to: $HOSTNAME"

# Use docker-compose exec to access the CTFd container and update the configuration
docker-compose exec ctfd python -c "
from CTFd.utils import set_config
set_config('whale:domain_hostname', '$HOSTNAME')
print('Hostname updated successfully!')
print('Please restart CTFd for changes to take effect.')
"

echo "To apply changes, restart CTFd with: docker-compose restart ctfd"
