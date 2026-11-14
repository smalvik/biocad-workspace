#!/bin/sh
# Read-only inventory. Never print .env, private keys, Docker Config.Env or full Nginx config.
set -eu
id
hostname
cat /etc/os-release
df -h /opt
free -m
docker version --format '{{.Server.Version}}'
docker compose version
docker ps --format '{{.Names}} | {{.Image}} | {{.Ports}} | project={{.Label "com.docker.compose.project"}}'
ss -ltn
if command -v nginx >/dev/null 2>&1; then
    nginx -v
    nginx -T 2>&1 | awk '/^[[:space:]]*(server_name|listen|ssl_certificate)[[:space:]]/ {print}'
fi
