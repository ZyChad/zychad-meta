#!/bin/bash
# Renouvellement SSL Let's Encrypt
# Usage: sudo ./scripts/renew-ssl.sh
# Cron: 0 3 1 * * /opt/zychad-meta/scripts/renew-ssl.sh

set -e
cd "$(dirname "$0")/.."

# Adapter le domaine si besoin
DOMAIN="${SSL_DOMAIN:-www.zychadmeta.com}"

echo "Arrêt Nginx..."
docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true

echo "Renouvellement certificat..."
certbot renew --quiet

echo "Copie des certificats..."
cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" nginx/ssl/
cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" nginx/ssl/

echo "Redémarrage Nginx..."
docker compose -f docker-compose.prod.yml start nginx

echo "SSL renouvelé."
