# Configuration SSL pour app.zychadmeta.com

## Problème

Sans SSL, le navigateur affiche "This site doesn't support a secure connection" et le flux d'authentification échoue.

## Solution : Let's Encrypt (gratuit)

### Sur le serveur Hetzner

```bash
cd ~/ZyChad-Meta
git pull   # pour récupérer le script et la config SSL

# Lancer le script (arrête Nginx, obtient le cert, redémarre)
bash scripts/setup-ssl-hetzner.sh
```

**Important :** Remplace `admin@zychadmeta.com` dans le script par ton email si besoin (pour les notifications Let's Encrypt).

### Sur Vercel

Ajoute ces variables d'environnement (Settings → Environment Variables) :

```
BOT_URL=https://app.zychadmeta.com
NEXT_PUBLIC_BOT_URL=https://app.zychadmeta.com
```

Puis redéploie le projet.

### Renouvellement automatique

Les certificats Let's Encrypt expirent après 90 jours. Pour le renouvellement automatique :

```bash
crontab -e
```

Ajoute :

```
0 3 * * * certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/app.zychadmeta.com/fullchain.pem /root/ZyChad-Meta/nginx/ssl/ && cp /etc/letsencrypt/live/app.zychadmeta.com/privkey.pem /root/ZyChad-Meta/nginx/ssl/ && docker compose -f /root/ZyChad-Meta/docker-compose.bot-only.yml restart nginx"
```

(Adapte le chemin `/root/ZyChad-Meta` si ton projet est ailleurs.)
