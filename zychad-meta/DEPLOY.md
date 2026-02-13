# Guide complet — Déploiement ZyChad Meta

Guide pas à pas pour héberger le bot et le site en production.

---

## 1. Choix du VPS (100 utilisateurs simultanés)

### Recommandation : **Hetzner Cloud**

Meilleur rapport qualité/prix en Europe. Datacenters en Allemagne, Finlande, USA, Singapour.

| Config | vCPU | RAM | SSD | Prix/mois | Usage |
|--------|------|-----|-----|-----------|-------|
| **CCX23** | 4 dédiés | 16 GB | 160 GB | ~25 € | Démarrage, ~30 users actifs |
| **CCX33** | 8 dédiés | 32 GB | 240 GB | ~48 € | **100 users** (recommandé) |
| **CCX43** | 16 dédiés | 64 GB | 360 GB | ~96 € | Pic de charge, 200+ users |

**Pour 100 personnes en simultané** : prends **CCX33** (8 vCPU, 32 GB RAM). Le traitement vidéo (FFmpeg) est gourmand en CPU ; avec 8 cœurs dédiés tu peux gérer ~8–12 encodages en parallèle. Les 100 users ne traitent pas tous en même temps.

### Alternatives

| Hébergeur | Avantages | Inconvénients |
|-----------|-----------|---------------|
| **DigitalOcean** | Interface simple, bonne doc | Plus cher (~80 € pour équivalent CCX33) |
| **OVH** | Français, prix corrects | Support parfois lent |
| **Scaleway** | Français, EU | Moins de choix de config |
| **Contabo** | Très pas cher | Support et stabilité variables |

---

## 2. Prérequis

- VPS avec Ubuntu 22.04 ou 24.04
- Domaine (ex. `zychadmeta.com`) pointant vers l’IP du serveur (A record)
- Base Neon configurée (ou Postgres local)

---

## 3. Connexion au serveur

```bash
ssh root@TON_IP
# ou
ssh ton_user@TON_IP
```

---

## 4. Préparer le serveur

```bash
# Mise à jour
sudo apt update && sudo apt upgrade -y

# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Se déconnecter puis reconnecter pour appliquer le groupe
exit
ssh ...
```

---

## 5. Cloner le projet

```bash
cd /opt
git clone https://github.com/TON_USER/zychad-meta.git
cd zychad-meta
```

Ou uploader les fichiers via SCP/SFTP.

---

## 6. Configurer les variables d'environnement

```bash
cp .env.example .env
nano .env
```

Remplir au minimum :

```env
# Auth
NEXTAUTH_URL=https://www.zychadmeta.com
NEXTAUTH_SECRET=<génère avec: openssl rand -base64 48>
AUTH_TRUST_HOST=true

# Base de données (Neon)
DATABASE_URL=postgresql://user:pass@host.neon.tech/neondb?sslmode=require

# Secret partagé bot ↔ Next.js (obligatoire pour le callback quota)
INTERNAL_SECRET=<même commande: openssl rand -base64 32>

# Paddle (quand prêt)
NEXT_PUBLIC_PADDLE_CLIENT_TOKEN=ptk_live_xxxx
NEXT_PUBLIC_PADDLE_ENV=production
PADDLE_API_KEY=pk_live_xxxx
PADDLE_WEBHOOK_SECRET=whsec_xxxx
PADDLE_STARTER_PRICE_ID=pri_xxxx
PADDLE_STARTER_YEARLY_PRICE_ID=pri_xxxx
PADDLE_PRO_PRICE_ID=pri_xxxx
PADDLE_PRO_YEARLY_PRICE_ID=pri_xxxx
PADDLE_AGENCY_PRICE_ID=pri_xxxx
PADDLE_AGENCY_YEARLY_PRICE_ID=pri_xxxx

# Google OAuth (optionnel)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

Générer les secrets :

```bash
openssl rand -base64 48   # NEXTAUTH_SECRET
openssl rand -base64 32   # INTERNAL_SECRET
```

---

## 7. SSL (HTTPS) avec Let's Encrypt

### Étape 1 : Obtenir les certificats

```bash
# Installer Certbot
sudo apt install certbot -y

# Arrêter tout ce qui écoute sur le port 80 (Docker pas encore lancé = OK)
sudo certbot certonly --standalone -d www.zychadmeta.com -d zychadmeta.com

# Les certificats sont dans :
# /etc/letsencrypt/live/www.zychadmeta.com/fullchain.pem
# /etc/letsencrypt/live/www.zychadmeta.com/privkey.pem
```

### Étape 2 : Copier dans le projet

```bash
cd /opt/zychad-meta
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/www.zychadmeta.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/www.zychadmeta.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl
```

### Étape 3 : Config Nginx avec SSL

```bash
cp nginx/nginx-ssl.conf.example nginx/nginx.conf
nano nginx/nginx.conf
# Remplacer TON_DOMAINE par www.zychadmeta.com (2 endroits)
```

---

## 8. Lancer les services

```bash
cd /opt/zychad-meta

# Build et démarrage
docker compose -f docker-compose.prod.yml up -d --build

# Migrer la base (une seule fois)
docker compose -f docker-compose.prod.yml exec web npx prisma db push
```

---

## 9. Vérifications

| URL | Attendu |
|-----|---------|
| https://www.zychadmeta.com | Landing page |
| https://www.zychadmeta.com/login | Page de connexion |
| https://www.zychadmeta.com/register | Inscription |
| https://www.zychadmeta.com/app/ | Redirection login si non connecté |
| https://www.zychadmeta.com/app/ (connecté) | Interface du bot |

---

## 10. Logs et dépannage

```bash
# Logs de tous les services
docker compose -f docker-compose.prod.yml logs -f

# Logs d'un service
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f bot
docker compose -f docker-compose.prod.yml logs -f nginx

# Redémarrer un service
docker compose -f docker-compose.prod.yml restart web
```

---

## 11. Renouvellement SSL (automatique)

Les certificats Let's Encrypt expirent après 90 jours.

```bash
# Test manuel
sudo certbot renew --dry-run

# Copier les nouveaux certs et redémarrer Nginx
sudo cp /etc/letsencrypt/live/www.zychadmeta.com/fullchain.pem /opt/zychad-meta/nginx/ssl/
sudo cp /etc/letsencrypt/live/www.zychadmeta.com/privkey.pem /opt/zychad-meta/nginx/ssl/
cd /opt/zychad-meta && docker compose -f docker-compose.prod.yml restart nginx
```

**Automatiser avec cron** :

Un script est fourni dans `scripts/renew-ssl.sh` :

```bash
chmod +x scripts/renew-ssl.sh
sudo crontab -e
# Ajouter (1er de chaque mois à 3h) :
0 3 1 * * /opt/zychad-meta/scripts/renew-ssl.sh
```

Adapte `SSL_DOMAIN` dans le script si ton domaine diffère de `www.zychadmeta.com`.

---

## 12. Mises à jour du code

```bash
cd /opt/zychad-meta
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 13. Architecture

```
                    Internet
                        │
                        ▼
                  Nginx (80/443)
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   /, /login      /api/*           /app/*
   /register      (auth, usage,    (bot)
   /billing       webhooks)
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
                  Next.js (web:3000)
                        │
                        ├── Prisma → Neon (PostgreSQL)
                        │
                        └── auth_request pour /app/*
                                    │
                                    ▼
                              Bot Python (bot:5000)
                                    │
                                    └── Callback /api/usage/increment
                                        après chaque traitement
```

---

## 14. Checklist finale

- [ ] Domaine pointant vers l'IP du VPS
- [ ] `.env` rempli (NEXTAUTH_URL, DATABASE_URL, INTERNAL_SECRET)
- [ ] Certificats SSL dans `nginx/ssl/`
- [ ] `nginx.conf` avec le bon domaine
- [ ] `docker compose -f docker-compose.prod.yml up -d --build`
- [ ] `prisma db push` exécuté
- [ ] Test : login → accès /app/ → traitement d'un fichier
