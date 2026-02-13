# Déploiement : Vercel (LP + Auth) + Hetzner (Bot)

Guide pour l’architecture avec LP sur Vercel et bot sur Hetzner.

---

## Architecture

| Service | Hébergement | URL |
|---------|-------------|-----|
| LP, Auth, Billing, Dashboard | **Vercel** | https://www.zychadmeta.com |
| Bot | **Hetzner** | https://app.zychadmeta.com |

---

## 1. Vercel

### Variables d'environnement

Dans le projet Vercel → Settings → Environment Variables :

```
NEXTAUTH_URL=https://www.zychadmeta.com
NEXTAUTH_SECRET=<ton secret>
BOT_URL=https://app.zychadmeta.com
NEXT_PUBLIC_BOT_URL=https://app.zychadmeta.com
```

Et les autres (DATABASE_URL, Paddle, Google, etc.).

### Déploiement

Le code a été mis à jour pour :
- Cookies avec `domain: ".zychadmeta.com"` (partagés entre www et app)
- Liens vers le bot via `BOT_URL`

Redéploie sur Vercel après ces changements.

---

## 2. DNS

Dans ton registrar (Cloudflare, OVH, etc.) :

| Type | Nom | Valeur |
|------|-----|--------|
| A ou CNAME | www | Vercel (ou cname.vercel-dns.com) |
| A | app | 46.225.122.166 |

---

## 3. Hetzner — Bot seul

### Arrêter l’ancien stack

```bash
cd /opt/zychad-meta
docker compose -f docker-compose.prod.yml down
```

### Fichiers à envoyer

Depuis ton PC :

```powershell
cd "C:\Users\PCZONE.GE\Documents\ZyChad Meta"
scp docker-compose.bot-only.yml root@46.225.122.166:/opt/zychad-meta/
scp nginx/nginx-bot-only.conf root@46.225.122.166:/opt/zychad-meta/nginx/
```

### .env sur le serveur

```bash
nano /opt/zychad-meta/.env
```

Conserver uniquement :

```
INTERNAL_SECRET=<ton secret>
```

Le bot appelle `https://www.zychadmeta.com/api/usage/increment` (déjà dans le compose).

### Lancer le bot

```bash
cd /opt/zychad-meta
docker compose -f docker-compose.bot-only.yml up -d --build
```

---

## 4. SSL pour app.zychadmeta.com (obligatoire)

Les cookies de session sont en `secure`, donc **app.zychadmeta.com doit être en HTTPS**.

Sur le serveur Hetzner :

```bash
# 1. Arrêter nginx pour libérer le port 80
docker compose -f docker-compose.bot-only.yml stop nginx

# 2. Obtenir le certificat
apt install certbot -y
certbot certonly --standalone -d app.zychadmeta.com

# 3. Copier les certs
cp /etc/letsencrypt/live/app.zychadmeta.com/fullchain.pem /opt/zychad-meta/nginx/ssl/
cp /etc/letsencrypt/live/app.zychadmeta.com/privkey.pem /opt/zychad-meta/nginx/ssl/

# 4. Utiliser la config SSL
cp /opt/zychad-meta/nginx/nginx-bot-only-ssl.conf.example /opt/zychad-meta/nginx/nginx-bot-only.conf

# 5. Mettre à jour le docker-compose pour utiliser nginx-bot-only.conf (déjà le cas)

# 6. Relancer
docker compose -f docker-compose.bot-only.yml up -d
```

---

## 5. Vérification

1. https://www.zychadmeta.com → LP
2. Inscription / connexion
3. https://app.zychadmeta.com → bot (après connexion)
4. Sans connexion → redirection vers login sur www

---

## Flux

```
User → app.zychadmeta.com
         │
         ▼
      Nginx (Hetzner)
         │
         ├─ auth_request → https://www.zychadmeta.com/api/auth/verify (avec Cookie)
         │
         ├─ 200 → proxy vers Bot
         ├─ 401 → redirect www.zychadmeta.com/login
         └─ 403 → redirect www.zychadmeta.com/billing?reason=quota
```
