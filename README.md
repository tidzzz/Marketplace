# API Abilan Tidiane

API minimaliste d’un marketplace seconde-main construite avec Flask + SQLAlchemy et une base SQLite. Elle expose des endpoints pour gérer les utilisateurs, catégories et adresses, avec un schéma OpenAPI fourni.

## Stack

- Python (Flask)
- SQLAlchemy (ORM) + SQLite
- Flask-CORS
- OpenAPI 3.1 (`full_openapi.yaml`)

## Structure du projet

```text
app.py                    # Entrée de l'application Flask (app:app)
full_openapi.yaml         # Spécification OpenAPI de référence (Tier A)
requirements.txt          # Dépendances Python
database/
  database.py             # Initialisation SQLAlchemy
  models.py               # Modèles User, Category, Address
  database.db             # Fichier SQLite (créé au premier run)
src/
  templates/
    layout.html.jinja2    # Template de test /test
```

## Lancer en local (dev)


1. Créez un environnement virtuel et installez les dépendances

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Démarrez l’API

```bash
python app.py
```

Par défaut, l’API écoute sur <http://127.0.0.1:5000>

Notes:

- La base SQLite est créée automatiquement (tables) au premier lancement.
- Le fichier cible attendu est `database/database.db`.

## Authentification de test (en-tête)

Pour les endpoints qui requièrent un utilisateur, utilisez l’en-tête HTTP suivant:

```text
X-User-Email: <email-utilisateur>
```

- L’admin de test est `admin@imt.test` (à utiliser pour les routes admin uniquement).
- Pour créer un utilisateur standard: `POST /api/users` avec `{ "email": "...", "password": "..." }`.

## Endpoints principaux (implémentés jusqu'à maintenant)

- `GET /api/categories` — liste toutes les catégories
- `POST /api/categories` — crée une catégorie (réservé admin: `X-User-Email: admin@imt.test`)
- `POST /api/users` — enregistre un utilisateur (hash du mot de passe)
- `GET /api/addresses` — liste les adresses de l’utilisateur connecté (en-tête requis)
- `POST /api/addresses` — crée une adresse pour l’utilisateur connecté
- `PUT /api/addresses/{id}` — modifie une adresse de l’utilisateur connecté
- `DELETE /api/addresses/{id}` — supprime une adresse de l’utilisateur connecté

Autres routes:

- `/` — ping simple
- `/test` — rend le template `layout.html.jinja2`

Pour une description complète de l’API cible (obligations côté tests), se référer à `full_openapi.yaml`.

## Exemples rapides (curl)

Créer un utilisateur:

```bash
curl -X POST http://127.0.0.1:5000/api/users \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}'
```

Lister ses adresses (avec authentification par en-tête):

```bash
curl -X GET http://127.0.0.1:5000/api/addresses \
  -H 'X-User-Email: alice@example.com'
```

Créer une catégorie (admin):

```bash
curl -X POST http://127.0.0.1:5000/api/categories \
  -H 'Content-Type: application/json' \
  -H 'X-User-Email: admin@imt.test' \
  -d '{"name":"Mode","parent_id":null}'
```

## Base de données

- Moteur: SQLite (fichier dans `database/database.db`).
- Initialisation: automatique au démarrage via `init_database()`.
- Réinitialiser (attention, destructive):

```bash
rm -f database/database.db
python app.py
```


## Dépannage

- 404 ou 401 sur des routes protégées: vérifiez l’en-tête `X-User-Email`.
- 403 sur création de catégories: l’en-tête doit être exactement `admin@imt.test`.
- Base non créée: supprimez `database/database.db` puis relancez; vérifiez que vous lancez depuis la racine du projet.


