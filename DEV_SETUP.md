# Setup ZyChad Meta SaaS

## Production (Docker)

```bash
# 1. Copier le bot (déjà fait si tu as cloné)
# cp ../zychad_metaV15.py processing/

# 2. Configurer .env
cp .env.example .env
# Éditer .env : NEXTAUTH_SECRET, DB_PASSWORD, INTERNAL_SECRET, Paddle keys

# 3. Lancer
docker compose up -d

# 4. Migrer la DB
docker compose exec web npx prisma db push
```

Nginx route :
- `/`, `/login`, `/register`, `/billing`, `/settings`, `/api/*` → Next.js
- `/app/*` → Bot (protégé par auth_request)

## Développement

### Sans Nginx (recommandé pour dev)

```bash
# Terminal 1 : Next.js
npm run dev

# Terminal 2 : Bot
cd processing && python zychad_metaV15.py

# Terminal 3 : DB (optionnel)
docker compose up postgres -d
npx prisma db push
```

- Landing, auth, billing, settings : http://localhost:3000
- Bot : http://localhost:61550 (ouvre directement)

### Avec Nginx (pour tester le flux complet)

```bash
docker compose -f docker-compose.dev.yml up -d
# ou configurer Nginx local
```

## Paddle

1. Crée les produits/prix dans Paddle Dashboard
2. Configure le webhook : `https://ton-domaine.com/api/webhooks/paddle`
3. Événements : subscription.created, subscription.updated, subscription.canceled, transaction.completed, subscription.past_due
