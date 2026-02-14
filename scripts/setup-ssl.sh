#!/bin/bash
# Script à exécuter sur le serveur Hetzner pour configurer SSL (Let's Encrypt)
# Usage: ./scripts/setup-ssl.sh [email]
#   email : ton email pour Let's Encrypt (ex: admin@zychadmeta.com)

set -e
DOMAIN="app.zychadmeta.com"
PROJECT_DIR="${2:-$HOME/ZyChad-Meta}"
EMAIL="${1:-}"

if [ -z "$EMAIL" ]; then
    echo "Usage: $0 ton@email.com [chemin_projet]"
    exit 1
fi

echo "🔐 Configuration SSL pour $DOMAIN"
echo "   Projet: $PROJECT_DIR"
echo ""

# Arrêter Nginx pour libérer le port 80
echo "1. Arrêt de Nginx..."
cd "$PROJECT_DIR"
docker compose -f docker-compose.bot-only.yml stop nginx 2>/dev/null || true

# Obtenir le certificat
echo "2. Obtention du certificat Let's Encrypt..."
if ! command -v certbot &>/dev/null; then
    echo "   Installation de certbot..."
    apt-get update && apt-get install -y certbot
fi

certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL"

# Copier les certificats
echo "3. Copie des certificats..."
mkdir -p "$PROJECT_DIR/nginx/ssl"
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$PROJECT_DIR/nginx/ssl/"
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem "$PROJECT_DIR/nginx/ssl/"
chmod 644 "$PROJECT_DIR/nginx/ssl/fullchain.pem"
chmod 600 "$PROJECT_DIR/nginx/ssl/privkey.pem"

# Redémarrer
echo "4. Redémarrage des services..."
docker compose -f docker-compose.bot-only.yml up -d

echo ""
echo "✅ SSL configuré ! https://$DOMAIN est prêt."
echo "   Renouvellement auto : certbot renew (ou cron)"
