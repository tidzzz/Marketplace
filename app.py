

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Configurer la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recommandé pour désactiver les notifications inutiles

# Créer l'objet qui représente la connexion à la base de données
db = SQLAlchemy(app)

# DÉFINITION DU MODÈLE USER
#    Cette classe hérite de db.Model. SQLAlchemy sait alors
#    qu'elle correspond à une table.
class User(db.Model):
    # __tablename__ est optionnel, mais c'est une bonne pratique de le nommer explicitement.
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    
    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(200), nullable=False)
    
    credits_cents = db.Column(db.Integer, nullable=False, default=0)

    
    def __repr__(self):
        return f'<User {self.email}>'



@app.route('/')
def hello():
    return "Le serveur est en marche !"

if __name__ == '__main__':
    app.run(debug=True, port=5000)