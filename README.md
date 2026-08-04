# CoDeCI — Backend API

API de la plateforme de collecte de déchets pour la Côte d'Ivoire.
FastAPI + PostgreSQL/PostGIS.

## Structure du projet

```
codeci-backend/
├── sql/schema.sql          Schéma SQL complet (documentation + création manuelle)
├── app/
│   ├── config.py           Configuration (variables d'environnement)
│   ├── database.py         Connexion SQLAlchemy à PostgreSQL
│   ├── main.py              Point d'entrée FastAPI
│   ├── models/               Modèles SQLAlchemy (une table = un modèle)
│   ├── schemas/              Schémas Pydantic (validation API)
│   ├── api/                  Endpoints (routers FastAPI)
│   └── services/
│       └── photo_verification.py   Vérification anti-fraude (EXIF + hash)
```

## Installation

### 1. Prérequis
- Python 3.11+
- PostgreSQL 15+ avec l'extension PostGIS installée

### 2. Créer la base de données

```bash
createdb codeci_db
psql codeci_db -c "CREATE EXTENSION postgis;"
psql codeci_db -f sql/schema.sql
psql codeci_db -f sql/seed_data.sql   # communes, opérateurs et catégories réels
```

`seed_data.sql` insère directement les données réelles du contexte
ivoirien : les 13 communes du District Autonome d'Abidjan, avec leur
opérateur de collecte réellement attitré (ECOTI SA ou ECO EBURNIE selon
la répartition officielle), ainsi que les 5 catégories de signalement
validées. **Attention** : les polygones géographiques de chaque commune
sont des rectangles approximatifs pour disposer de données de test
plausibles — à remplacer par les vraies limites administratives
(shapefiles ANSTAT/INS) avant un déploiement réel.

### 3. Installer les dépendances Python

```bash
python3 -m venv venv
source venv/bin/activate   # sous Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
# Puis éditer .env avec tes propres identifiants PostgreSQL
```

### 5. Lancer le serveur de développement

```bash
uvicorn app.main:app --reload
```

L'API est alors accessible sur http://localhost:8000
La documentation interactive (générée automatiquement par FastAPI) est sur http://localhost:8000/docs

## Tester le premier endpoint

Le endpoint `POST /signalements` accepte un formulaire multipart avec :
- `utilisateur_id`, `categorie_id`, `commune_id` (UUID)
- `latitude`, `longitude` (nombres décimaux)
- `bac_id` (UUID, optionnel)
- `mode_soumission` (`en_ligne` ou `hors_ligne`)
- `photo` (fichier image)

Pour tester rapidement, utilise l'interface Swagger sur `/docs` — tu peux
y uploader une photo directement depuis le navigateur sans écrire de code.

**Important** : avant de pouvoir créer un signalement, il faut d'abord
insérer manuellement au moins une commune, un utilisateur et une catégorie
en base (via `psql` ou un futur endpoint d'administration).

## Prochaines étapes de développement

1. Endpoints CRUD pour Communes, Entreprises, Utilisateurs, Catégories
2. Endpoint de connexion/authentification (téléphone + OTP)
3. Endpoint de validation chauffeur (photo "après passage")
4. Tâche planifiée de suppression des photos après 90 jours (rétention)
5. Endpoints du dashboard web (heatmap, statistiques, gestion des rôles)
