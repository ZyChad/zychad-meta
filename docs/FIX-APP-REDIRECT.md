# Fix : app.zychadmeta.com redirige vers le dashboard

## Problème

Quand tu cliques sur "Accéder au bot" ou que tu vas sur app.zychadmeta.com, tu arrives sur zychadmeta.com/dashboard au lieu du bot.

## Cause

**app.zychadmeta.com pointe vers Vercel** au lieu de Hetzner. Le trafic va donc vers le site Next.js, qui redirige les utilisateurs connectés vers le dashboard.

## Solution

### 1. Vérifier / retirer app.zychadmeta.com de Vercel

1. Va sur **https://vercel.com** → ton projet ZyChad Meta
2. **Settings** → **Domains**
3. Si **app.zychadmeta.com** est listé → **Supprime-le**
4. Sur Vercel, il ne doit rester que : **www.zychadmeta.com** et **zychadmeta.com**

### 2. Configurer le DNS pour app.zychadmeta.com

Chez ton registrar DNS (Cloudflare, OVH, Namecheap, etc.) :

| Type | Nom | Valeur | TTL |
|------|-----|--------|-----|
| **A** | **app** | **46.225.122.166** | 300 |

*(Remplace 46.225.122.166 par l’IP de ton serveur Hetzner si elle est différente.)*

**Important :** Pas de CNAME vers Vercel pour `app`. Un seul enregistrement A vers l’IP Hetzner.

### 3. Vérifier

Après propagation DNS (quelques minutes) :

```bash
nslookup app.zychadmeta.com
```

L’IP renvoyée doit être celle de ton serveur Hetzner (46.225.122.166).

### 4. Tester

1. Va sur https://www.zychadmeta.com
2. Connecte-toi
3. Clique sur « Accéder au bot »
4. Tu dois arriver sur le bot (app.zychadmeta.com)
