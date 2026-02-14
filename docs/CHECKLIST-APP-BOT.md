# Checklist : app.zychadmeta.com et le bot

## Si tu as une 404 en accédant au bot

### 1. DNS : app.zychadmeta.com doit pointer vers Hetzner

Chez ton registrar DNS (Cloudflare, OVH, etc.) :

| Type | Nom | Valeur |
|------|-----|--------|
| **A** | **app** | **46.225.122.166** |

**Important :** Pas de CNAME vers Vercel pour `app`. Un seul enregistrement A vers l’IP Hetzner.

### 2. Vercel : app.zychadmeta.com ne doit PAS être dans les domaines

- Vercel → Settings → Domains
- Si **app.zychadmeta.com** est listé → **supprime-le**
- Seuls **www.zychadmeta.com** et **zychadmeta.com** doivent rester

### 3. Déployer le bot sur Hetzner

```bash
ssh root@46.225.122.166
cd ~/ZyChad-Meta
git pull
docker compose -f docker-compose.bot-only.yml up -d --build
```

### 4. Mettre à jour la config Nginx sur Hetzner

Si tu as créé `nginx-bot-only.conf` à la main, ajoute cette ligne dans le bloc `location = /auth/verify` :

```nginx
proxy_set_header X-Original-Host $host;
```

Puis redémarre Nginx :

```bash
docker compose -f docker-compose.bot-only.yml restart nginx
```

---

## Sécurité : quota et token

- **Token obligatoire** : pour accéder au bot via app.zychadmeta.com, un token JWT est requis (pas de cookie seul).
- **Quota** : vérifié à chaque requête par l’API verify.
- **Usage** : incrémenté quand le bot termine un traitement (INTERNAL_SECRET doit être identique sur Hetzner et Vercel).
