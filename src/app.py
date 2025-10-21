

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configurer la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recommandé pour désactiver les notifications inutiles

db = SQLAlchemy(app)


# DÉFINITION DU MODÈLE USER
#    Cette classe hérite de db.Model. SQLAlchemy sait alors
#    qu'elle correspond à une table.
class User(db.Model): # type: ignore
    # __tablename__ est optionnel, mais c'est une bonne pratique de le nommer explicitement.
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    credits_cents = db.Column(db.Integer, nullable=False, default=0)

    
    def __repr__(self):
        return f'<User {self.email}>'


@app.route('/api/users', methods=['POST'])
def register_user():
    
    data = request.get_json()

    
    if not data or not 'email' in data or not 'password' in data:
        return jsonify({"error": "Bad request: missing email or password"}), 400

    email = data['email']
    password = data['password']

    # Vérifier si l'utilisateur existe déjà dans la base de données
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Conflict: email already exists"}), 409

    # Hacher le mot de passe pour des raisons de sécurité
    hashed_password = generate_password_hash(password)

    # Créer une nouvelle instance de notre modèle User
    new_user = User(
        email=email,
        password_hash=hashed_password,
        credits_cents=0 
    )

    # Ajouter le nouvel utilisateur à la session et l'enregistrer dans la BDD
    db.session.add(new_user)
    db.session.commit()

    # Préparer et renvoyer la réponse de succès
    response_data = {
        "email": new_user.email,
        "credits_cents": new_user.credits_cents
    }
    return jsonify(response_data), 201


@app.route('/')
def hello():
    return "Le serveur est en marche !"

@app.route('/test',methods=['GET'])
def test():
    return render_template("layout.html.jinja2")

if __name__ == '__main__':
    
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

