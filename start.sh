#!/bin/bash

# Nom du dossier de l'environnement virtuel
VENV_DIR="venv"

# Vérifier si l'environnement virtuel existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv $VENV_DIR
fi

# Activer l'environnement virtuel
source $VENV_DIR/bin/activate

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Lancer l'application
echo "Démarrage de l'application..."
python app.py
