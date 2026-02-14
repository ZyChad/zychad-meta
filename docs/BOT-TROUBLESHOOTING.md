# Dépannage du bot (app.zychadmeta.com)

## 1. Essai illimité (quota non incrémenté)

**Cause :** Le bot n’arrive pas à appeler l’API Vercel pour incrémenter l’usage.

**À vérifier :**

### INTERNAL_SECRET identique partout

Sur **Hetzner** (`.env`) et sur **Vercel** (Settings → Environment Variables), `INTERNAL_SECRET` doit être **exactement le même**.

```bash
# Sur Hetzner, vérifier :
grep INTERNAL_SECRET .env
```

Sur Vercel : Settings → Environment Variables → `INTERNAL_SECRET`.

### Vérifier les logs du bot

```bash
docker compose -f docker-compose.bot-only.yml logs bot --tail 100
```

Si l’appel à `www.zychadmeta.com/api/usage/increment` échoue (401, timeout, etc.), le quota ne sera pas incrémenté.

---

## 2. Preview ne s’affiche pas

**Causes possibles :**

1. **Fichiers non déposés** : glisser-déposer des fichiers avant de cliquer sur Preview.
2. **Erreur de traitement** : vérifier les logs du bot pour des erreurs ffmpeg ou de traitement.
3. **Chemin de fichier** : en Docker, les chemins sont dans le conteneur ; si le preview échoue, regarder les logs.

```bash
docker compose -f docker-compose.bot-only.yml logs bot --tail 50
```

---

## 3. Envoi Telegram ne fonctionne pas

**À configurer :**

1. **Bot Telegram** : créer un bot via [@BotFather](https://t.me/BotFather) et récupérer le token.
2. **Connexion** : dans le bot, cliquer sur « Connecter Telegram » et coller le token.
3. **Chat ID** : obtenir ton Chat ID (ex. via [@userinfobot](https://t.me/userinfobot)) et le renseigner dans le champ « Chat ID ».
4. **Démarrer le bot** : envoyer `/start` à ton bot Telegram avant d’utiliser l’envoi.

---

## Checklist rapide

| Élément | Où vérifier |
|--------|-------------|
| `INTERNAL_SECRET` identique | Hetzner `.env` + Vercel env vars |
| `WEB_URL=https://www.zychadmeta.com` | docker-compose / .env Hetzner |
| Bot Telegram configuré | Interface du bot + Chat ID |
| Fichiers déposés avant Preview | Glisser-déposer dans la zone |
