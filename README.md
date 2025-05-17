# CTF PLATFORM
docker swarm init
docker node update --label-add='name=linux-1' $(docker node ls -q)


docker pull tryptoph/cloudshare-challenge:latest
docker pull tryptoph/path-traversal-challenge:latest
docker pull tryptoph/blogconnect-rfi:latest
docker pull tryptoph/ssrf-challenge:latest
docker pull tryptoph/bookreviewz-xss-challenge:latest
docker pull tryptoph/level1-web_challenge:latest
docker pull tryptoph/updateme:latest
docker pull tryptoph/my-kali-desktop:1.14.0


docker compose up --build -d
