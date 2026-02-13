# PROMPT CURSOR — ZyChad Meta SaaS

Lis ce prompt EN ENTIER avant de coder quoi que ce soit.

---

## LE CONCEPT

Le **bot Python** (`zychad_metaV15.py`) tourne avec son interface web complète (drop zone, slider variantes, mode selector, progress, download, scraper). **On vend l'accès au bot tel quel.**

L'utilisateur :
1. Arrive sur la **landing page**
2. S'inscrit / se connecte
3. Paie via Paddle
4. Est redirigé vers **le bot lui-même** — la même interface, le même visuel
5. Le bot tourne sur **ton serveur**, l'utilisateur n'installe rien

**On ne recrée PAS l'interface du bot en React. On utilise le bot directement, protégé derrière l'auth et le paiement.**

---

## ARCHITECTURE

```
Nginx (port 80/443)
├── /, /login, /register, /billing, /settings, /api/* → Next.js (port 3000)
└── /app/* → Bot Flask (port 5000) avec auth_request (vérifie session + quota)
```

**Nginx auth_request** : Chaque requête vers `/app/*` passe d'abord par Next.js `/api/auth/verify` pour vérifier session + quota. Si OK → proxy vers le bot. Sinon → 401 login ou 403 billing.

---

## CE QUE TU NE FAIS PAS

- ❌ NE PAS recréer l'interface du bot en React
- ❌ NE PAS utiliser d'iframe
- ❌ NE PAS ajouter BullMQ, Redis queue, S3, workers séparés
- ❌ NE PAS modifier la logique de traitement du bot (sauf callback quota)

---

## STACK

- Next.js 14 — Landing, Auth, Paddle, Billing, Settings
- NextAuth.js — Auth (email/password + Google)
- Prisma + PostgreSQL
- Paddle Billing
- Nginx — Reverse proxy + auth_request
- Bot Flask (zychad_metaV15.py) — Le produit, dans processing/
- Docker Compose

---

## FICHIERS CLÉS

- `nginx/nginx.conf` — Routing + auth_request
- `src/app/api/auth/verify/route.ts` — Vérification session + quota
- `src/app/api/usage/increment/route.ts` — Le bot appelle ça après chaque traitement
- `src/app/api/webhooks/paddle/route.ts` — Webhooks Paddle
- `processing/zychad_metaV15.py` — Le bot (avec callback quota)
- `processing/Dockerfile` — Image du bot

---

## PLANS

| | FREE | STARTER | PRO | AGENCY |
|---|---|---|---|---|
| Prix | 0€ | 29€/mois (23€ annuel) | 79€/mois (63€ annuel) | 199€/mois (159€ annuel) |
| Fichiers | 3 à VIE | 200/mois | 1000/mois | Illimité |

FREE = 3 uniquifications TOTALES à vie. Après → redirect `/billing?reason=quota`.
