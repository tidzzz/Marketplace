

from flask import Flask, jsonify, request, render_template
from database.database import db, init_database
from database.models import *
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# Configurer la base de données
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../database/database.db" #precise the place of the database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recommandé pour désactiver les notifications inutiles

db.init_app(app) # (1) flask prend en compte la base de donnee
with app.test_request_context(): # (2) bloc exécuté à l'initialisation de Flask
    init_database()


# DÉCORATEUR POUR PROTÉGER LES ROUTES ADMIN
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # On vérifie la présence et la valeur de l'en-tête X-User-Email
        if request.headers.get('X-User-Email') != 'admin@imt.test':
            # Si ce n'est pas l'admin, on renvoie une erreur 403 Forbidden
            return jsonify({"error": "Forbidden: admin only"}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/categories', methods=['GET'])
def list_categories():
    #Récupérer toutes les catégories de la base de données
    categories = Category.query.all()
    
    #Convertir chaque objet Category en dictionnaire
    categories_list = [category.to_dict() for category in categories]
    
    #Renvoyer la liste en JSON
    return jsonify(categories_list), 200


@app.route('/api/categories', methods=['POST'])
@admin_required 
def create_category():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Bad request: missing name"}), 400

    name = data['name']
    # parent_id est optionnel, on utilise .get() pour éviter une erreur s'il est absent
    parent_id = data.get('parent_id') 

    new_category = Category(name=name, parent_id=parent_id)
    
    db.session.add(new_category)
    db.session.commit()
    
    return jsonify(new_category.to_dict()), 201




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
    app.run(debug=True, port=5000)
