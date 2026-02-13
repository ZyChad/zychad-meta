#!/bin/bash
# Configuration SSL pour app.zychadmeta.com sur Hetzner
# À exécuter sur le serveur : bash scripts/setup-ssl-hetzner.sh

set -e
cd "$(dirname "$0")/.."

echo "=== Configuration SSL pour app.zychadmeta.com ==="

# 1. Arrêter Nginx pour libérer le port 80
echo "[1/5] Arrêt de Nginx..."
docker compose -f docker-compose.bot-only.yml stop nginx

# 2. Installer Certbot si nécessaire
if ! command -v certbot &> /dev/null; then
    echo "[2/5] Installation de Certbot..."
    apt-get update && apt-get install -y certbot
else
    echo "[2/5] Certbot déjà installé."
fi

# 3. Obtenir le certificat
echo "[3/5] Obtention du certificat Let's Encrypt..."
certbot certonly --standalone -d app.zychadmeta.com --non-interactive --agree-tos --email admin@zychadmeta.com --preferred-challenges http

# 4. Copier les certificats
echo "[4/5] Copie des certificats..."
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/app.zychadmeta.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/app.zychadmeta.com/privkey.pem nginx/ssl/
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem

# 5. Basculer sur la config SSL et redémarrer
echo "[5/5] Activation de la config SSL..."
if [ -f nginx/nginx-bot-only-ssl.conf ]; then
    cp nginx/nginx-bot-only.conf nginx/nginx-bot-only-http-backup.conf 2>/dev/null || true
    cp nginx/nginx-bot-only-ssl.conf nginx/nginx-bot-only.conf
else
    echo "Erreur: nginx/nginx-bot-only-ssl.conf introuvable. Fais git pull."
    docker compose -f docker-compose.bot-only.yml start nginx
    exit 1
fi

docker compose -f docker-compose.bot-only.yml start nginx

echo ""
echo "=== SSL configuré avec succès ! ==="
echo "Tu peux maintenant accéder à https://app.zychadmeta.com"
echo ""
echo "Renouvellement automatique : ajoute à crontab -e :"
echo "0 3 * * * certbot renew --quiet --deploy-hook 'docker compose -f /root/ZyChad-Meta/docker-compose.bot-only.yml restart nginx'"
