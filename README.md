# TikTok Auto-Montage — Guide de déploiement

## Étape 1 — Configurer Supabase

1. Va sur app.supabase.com et ouvre ton projet
2. Clique sur "SQL Editor" dans le menu à gauche
3. Colle le contenu du fichier `supabase_setup.sql` et clique "Run"
4. Va dans "Storage" et crée 3 buckets :
   - `clips` (public)
   - `sounds` (public)
   - `output` (public)
5. Pour chaque bucket, va dans "Policies" et ajoute une policy "Allow public access"
6. Note tes clés : va dans "Settings > API" et copie :
   - `Project URL`
   - `anon public key`

## Étape 2 — Déployer sur Railway

1. Va sur railway.app
2. Clique "New Project" > "Deploy from GitHub repo"
3. Connecte ton GitHub et sélectionne ce repo
4. Railway va détecter le Dockerfile automatiquement
5. Une fois déployé, va dans "Variables" et ajoute :
   - `SUPABASE_URL` = ta Project URL Supabase
   - `SUPABASE_KEY` = ton anon public key Supabase
   - `ANTHROPIC_API_KEY` = ta clé API Anthropic (sk-ant-...)
6. Railway va redémarrer l'app automatiquement

## Étape 3 — Utiliser l'app

1. Récupère l'URL de ton app Railway (ex: https://ton-app.railway.app)
2. Va sur `/bibliotheque` pour uploader tes clips et effets sonores
3. Va sur `/creer` pour générer tes vidéos

## Structure du projet

```
tiktok-saas/
├── Dockerfile
├── supabase_setup.sql
├── backend/
│   ├── app.py          # Serveur Flask + logique IA + FFmpeg
│   └── requirements.txt
└── frontend/
    └── templates/
        ├── index.html       # Page d'accueil
        ├── bibliotheque.html # Gestion clips et sons
        └── creer.html       # Création de vidéos
```
