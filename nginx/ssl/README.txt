Place tes certificats SSL ici :
- fullchain.pem (certificat)
- privkey.pem (clé privée)

Génération automatique (sur le serveur Hetzner) :
  chmod +x scripts/setup-ssl.sh
  ./scripts/setup-ssl.sh ton@email.com

Génération manuelle avec Certbot :
  certbot certonly --standalone -d app.zychadmeta.com
  cp /etc/letsencrypt/live/app.zychadmeta.com/*.pem nginx/ssl/
