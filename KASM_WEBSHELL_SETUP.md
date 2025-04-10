# Kasm WebShell Integration Guide

This guide explains how to properly set up and use Kasm Web desktop environments with the CTFd WebShell plugin.

## Overview

The CTFd WebShell plugin has been modified to work with Kasm Web containers, which provide a more modern and feature-rich web-based desktop experience than traditional VNC setups.

### Key Changes Made

1. Updated the desktop URL protocol from HTTP to HTTPS (Kasm requires HTTPS)
2. Added proper environment variables for Kasm authentication
3. Added shared memory configuration required by Kasm containers
4. Updated port mappings to use the standard Kasm port (6901)
5. Added additional UI elements to handle HTTPS certificates better

## Setup Instructions

### 1. Run the Update Script

First, run the provided update script to ensure all configurations are set correctly:

```bash
chmod +x update_webshell_kasm.sh
./update_webshell_kasm.sh
```

### 2. Update WebShell Images in Admin Panel

Go to the WebShell admin panel and ensure your images are configured correctly:

- **Docker Image**: Use Kasm images like `kasmweb/kali-rolling-desktop:1.14.0`
- **Port Settings**: Both shell port and desktop port should be set to `6901`
- **Memory Limit**: At least `512m`, recommended `1024m` or higher
- **CPU Limit**: At least `0.5`, recommended `1.0` or higher

### 3. Restart CTFd

Restart your CTFd instance to apply all changes:

```bash
# For Docker setups
docker-compose restart

# For direct installations
systemctl restart ctfd  # or appropriate service restart command
```

## Using Kasm Web Desktops

When accessing Kasm desktops, keep in mind:

1. **HTTPS is Required**: Kasm uses HTTPS by default. You may need to accept self-signed certificates.
2. **Direct Links**: If the embedded iframe doesn't load properly, use the "Open in New Tab" option.
3. **Authentication**: The password is automatically passed to the Kasm container.

## Troubleshooting

### Common Issues

1. **Desktop Shows "Connection Failed"**
   - Ensure the container has finished starting (usually takes 20-30 seconds)
   - Try accessing via the direct URL link
   - Check browser console for certificate/HTTPS errors

2. **Certificate Warnings**
   - This is normal for self-signed certificates. Click "Advanced" and "Proceed" in your browser.

3. **Performance Issues**
   - Increase the memory and CPU limits for the container
   - Consider reducing the desktop resolution in Kasm settings

4. **Container Not Starting**
   - Check logs for any errors: `docker logs <container_id>`
   - Ensure Docker has enough resources allocated

## Supported Kasm Images

The following Kasm images are recommended for CTFd WebShell:

- `kasmweb/kali-rolling-desktop:1.14.0` - Full Kali Linux with desktop
- `kasmweb/terminal:1.14.0-security` - Security-focused terminal
- `kasmweb/core-ubuntu-focal:1.14.0-security` - Ubuntu with security tools

## Additional Resources

- [Kasm Workspaces Documentation](https://www.kasmweb.com/docs/)
- [Kasm Docker Images](https://hub.docker.com/u/kasmweb)
