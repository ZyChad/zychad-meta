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

Si app est sur Vercel, tu auras une 404 car Vercel ne sert pas le bot.

### 3. Config Nginx : passer le token à verify

**Problème :** Nginx `auth_request` n'envoie pas les paramètres de requête. Le token `?token=xxx` n'arrivait pas à verify.

**Solution :** Les configs ont été corrigées avec `set $token $arg_token` et `proxy_pass .../verify?token=$token`.

### 4. HTTPS : utiliser la config SSL

Si tu utilises `https://app.zychadmeta.com`, dans `docker-compose.bot-only.yml` remplace `nginx-bot-only.conf` par `nginx-bot-only-ssl.conf` dans les volumes. Place les certificats dans `nginx/ssl/`.

### 5. Déployer sur Hetzner

```bash
ssh root@46.225.122.166
cd ~/ZyChad-Meta
git pull
docker compose -f docker-compose.bot-only.yml up -d --build
docker compose -f docker-compose.bot-only.yml restart nginx
```

### 6. Vérifier le flux

1. Va sur www.zychadmeta.com, connecte-toi
2. Clique sur « Ouvrir le bot » dans le dashboard
3. Tu dois être redirigé vers app.zychadmeta.com/?token=xxx
4. Le bot doit s'afficher

---

## Sécurité : quota et token

- **Token obligatoire** : pour accéder au bot via app.zychadmeta.com, un token JWT est requis (pas de cookie seul).
- **Quota** : vérifié à chaque requête par l’API verify.
- **Usage** : incrémenté quand le bot termine un traitement (INTERNAL_SECRET doit être identique sur Hetzner et Vercel).
