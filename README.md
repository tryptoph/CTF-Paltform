# CTF Platform

A comprehensive Capture The Flag (CTF) platform featuring multiple web security challenges designed to help you practice and improve your cybersecurity skills.

## Overview

This platform contains various intentionally vulnerable web applications that cover common security vulnerabilities including path traversal, remote file inclusion (RFI), server-side request forgery (SSRF), cross-site scripting (XSS), and more. The platform includes a Kali Linux desktop environment to provide all the necessary tools for solving the challenges.


## Installation

1. Clone this repository:
   ```
   git clone https://github.com/tryptoph/CTF-Paltform.git
   cd ctf-platform
   ```

2. Initialize Docker Swarm:
   ```
   docker swarm init
   ```

3. Label the node:
   ```
   docker node update --label-add='name=linux-1' $(docker node ls -q)
   ```

4. Pull the required Docker images:
   ```
   docker pull tryptoph/cloudshare-challenge:latest
   docker pull tryptoph/path-traversal-challenge:latest
   docker pull tryptoph/blogconnect-rfi:latest
   docker pull tryptoph/ssrf-challenge:latest
   docker pull tryptoph/bookreviewz-xss-challenge:latest
   docker pull tryptoph/level1-web_challenge:latest
   docker pull tryptoph/updateme:latest
   docker pull tryptoph/my-kali-desktop:1.14.0
   ```

5. Start the CTF platform:
   ```
   docker compose up --build -d
   ```

## Accessing the Platform

Once the platform is running, you can access it through your web browser:

- Main CTF platform: http://localhost:8000



## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
