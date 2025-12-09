# API Abilan Tidiane - IMT Second-Hand Marketplace

Ce projet est une application web de type "marketplace" de seconde main, développée avec Flask. Elle fournit une API REST pour la gestion des utilisateurs, des catégories, des annonces et des transactions, ainsi qu'une interface utilisateur basique rendue avec des templates Jinja2.

## Stack Technique

- **Langage** : Python 3.8+
- **Framework Web** : Flask
- **ORM** : SQLAlchemy
- **Base de données** : SQLite
- **API Spec** : OpenAPI 3.1 (`full_openapi.yaml`)

## Structure du Projet

```text
app.py                    # Point d'entrée de l'application Flask
full_openapi.yaml         # Spécification OpenAPI
requirements.txt          # Dépendances Python
start.sh                  # Script de démarrage rapide
tests/                    # Dossier des tests
  test_scenario.py        # Scénarios de test reproductibles
database/
  database.py             # Initialisation DB
  models.py               # Modèles de données
  database.db             # Fichier SQLite (généré)
src/
  templates/              # Templates Jinja2
instance/
  uploads/                # Stockage des fichiers uploadés
```

## Installation et Démarrage

### Option 1 : Démarrage Rapide (macOS/Linux)

Un script `start.sh` est fourni pour automatiser la création de l'environnement virtuel, l'installation des dépendances et le lancement de l'application.

```bash
chmod +x start.sh
./start.sh
```

### Option 2 : Installation Manuelle

1. **Créer un environnement virtuel** :

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # ou
    venv\Scripts\activate     # Windows
    ```

2. **Installer les dépendances** :

    ```bash
    pip install -r requirements.txt
    ```

3. **Lancer l'application** :

    ```bash
    python app.py
    ```

L'application sera accessible à l'adresse : `http://127.0.0.1:5000`.

## Utilisation de l'API

L'API suit la spécification définie dans `full_openapi.yaml`.

### Authentification

L'authentification pour les tests et l'API se fait via le header HTTP `X-User-Email`.

- **Admin** : `admin@imt.test` (pour les opérations privilégiées comme la création de catégories)
- **Utilisateur Standard** : Tout email enregistré via `POST /api/users`.

### Exemples (cURL)

**Créer une catégorie (Admin uniquement)** :

```bash
curl -X POST http://127.0.0.1:5000/api/categories \
  -H 'Content-Type: application/json' \
  -H 'X-User-Email: admin@imt.test' \
  -d '{"name":"Informatique"}'
```

**Lister les catégories** :

```bash
curl -X GET http://127.0.0.1:5000/api/categories
```

## Tests Reproductibles

Des scénarios de test automatisés sont disponibles dans le dossier `tests/`. Ces tests utilisent une base de données en mémoire pour ne pas affecter vos données locales.

Pour exécuter les tests :

```bash
# Assurez-vous d'être dans l'environnement virtuel
source venv/bin/activate

# Lancer les tests
python -m unittest discover tests
```

Le fichier `tests/test_scenario.py` contient un scénario complet vérifiant :

1. L'état initial (vide).
2. La création de catégorie par un admin.
3. La persistance et la récupération des données.
4. La sécurité (refus de création pour les non-admins).


