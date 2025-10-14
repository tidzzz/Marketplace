

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Configurer la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recommandé pour désactiver les notifications inutiles

# Créer l'objet qui représente la connexion à la base de données
db = SQLAlchemy(app)

# --- On définira les modèles (tables) ici plus tard ---



@app.route('/')
def hello():
    return "Le serveur est en marche !"

if __name__ == '__main__':
    app.run(debug=True, port=5000)