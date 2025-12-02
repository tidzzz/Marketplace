from functools import wraps
import os
from flask import Flask, jsonify, request, render_template, make_response #, url_for, redirect
from flask_cors import CORS
from database.database import db, init_database
from database.models import *
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app
     #,origins=[]
     )

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
        # Vérifie l'en-tête X-User-Email pour l'accès admin
        user_email = request.headers.get('X-User-Email')
        if not isinstance(user_email, str) or user_email.strip().lower() != 'admin@imt.test':
            return jsonify({"error": "Forbidden: admin only"}), 403
        return f(*args, **kwargs)
    return decorated_function

# DÉCORATEUR POUR AUTHENTIFIER L'UTILISATEUR
def authenticated_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_email = request.headers.get('X-User-Email')
        if not user_email:
            return jsonify({"error": "Unauthorized: missing X-User-Email"}), 401
        
        # Vérifier que l'utilisateur existe
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({"error": "Unauthorized: invalid user"}), 401
        
        # Passer l'utilisateur à la fonction
        return f(user, *args, **kwargs)
    return decorated_function


#-------------------------CATEGORIES--------------------------#

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


@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Not found"}), 404
    
    if Category.query.filter_by(parent_id=category_id).first():
        return jsonify({"error": "Conflict: category has children or listings"}), 409
        
    if Listing.query.filter_by(category_id=category_id).first():
        return jsonify({"error": "Conflict: category has children or listings"}), 409
    
    db.session.delete(category)
    db.session.commit()
    
    return '', 204


#-------------------------USERS--------------------------#

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


#-------------------------ADDRESSES--------------------------#

@app.route('/api/addresses',methods=['GET'])
@authenticated_required
def api_addresses_get(user):
    addresses = Address.query.filter_by(user_email=user.email).all()
    addresses_list = [address.to_dict() for address in addresses]
    return jsonify(addresses_list), 200

@app.route('/api/addresses', methods=['POST'])
@authenticated_required
def api_addresses_post(user):
    data = request.get_json()
    
    # Validation des champs obligatoires
    if not data or 'line1' not in data or 'city' not in data or 'postal_code' not in data:
        return jsonify({"error": "Bad request: missing required fields"}), 400
    
    try:
        new_address = Address(
            line1=data['line1'],
            line2=data.get('line2'), 
            city=data['city'],
            postal_code=data['postal_code'],
            user_email=user.email
        )
        
        db.session.add(new_address)
        db.session.commit()
        
        return jsonify(new_address.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Bad request: {str(e)}"}), 400

@app.route('/api/addresses/<int:address_id>', methods=['PUT'])
@authenticated_required
def api_addresses_put(user, address_id):
    """Modifier une adresse existante"""
    address = Address.query.filter_by(id=address_id, user_email=user.email).first()
    
    if not address:
        return jsonify({"error": "Not found: address does not exist or does not belong to user"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Bad request: no data provided"}), 400
    
    try:
        # Mettre à jour uniquement les champs fournis
        if 'line1' in data:
            address.line1 = data['line1']
        if 'line2' in data:
            address.line2 = data['line2']
        if 'city' in data:
            address.city = data['city']
        if 'postal_code' in data:
            address.postal_code = data['postal_code']
        
        db.session.commit()
        return jsonify(address.to_dict()), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Bad request: {str(e)}"}), 400
    
@app.route('/api/addresses/<int:address_id>', methods=['DELETE'])
@authenticated_required
def api_addresses_delete(user, address_id):
    """Supprimer une adresse"""
    address = Address.query.filter_by(id=address_id, user_email=user.email).first()
    
    if not address:
        return jsonify({"error": "Not found: address does not exist or does not belong to user"}), 404
    
    db.session.delete(address)
    db.session.commit()
    
    return '', 204  # No Content


#-------------------------LISTINGS--------------------------#

@app.route('/api/listings', methods=['POST'])
@authenticated_required
def create_listing(user):
    data = request.get_json()
    
    # Validation des champs obligatoires
    required_fields = ['title', 'description', 'price_cents', 'shipping_cents', 'category_id', 'photos']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Bad request: missing {field}"}), 400
            
    photos_data = data['photos']
    if not isinstance(photos_data, list) or len(photos_data) < 1:
        return jsonify({"error": "Bad request: photos must be a non-empty list"}), 400
    if len(photos_data) > 12:
         return jsonify({"error": "Bad request: too many photos (max 12)"}), 400

    # Validation de la catégorie
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({"error": "Bad request: invalid category_id"}), 400

    try:
        new_listing = Listing(
            seller_email=user.email,
            title=data['title'],
            description=data['description'],
            price_cents=data['price_cents'],
            shipping_cents=data['shipping_cents'],
            category_id=data['category_id']
        )
        
        # Gestion des photos
        thumbnail_count = sum(1 for p in photos_data if p.get('is_thumbnail', False))
        if thumbnail_count > 1:
             return jsonify({"error": "Bad request: at most one photo can be a thumbnail"}), 400
        
        listing_photos = []
        for photo_data in photos_data:
            if 'url' not in photo_data:
                 return jsonify({"error": "Bad request: photo missing url"}), 400
            
            is_thumbnail = photo_data.get('is_thumbnail', False)
            listing_photos.append(ListingPhoto(url=photo_data['url'], is_thumbnail=is_thumbnail))
            
        # Si aucune miniature n'a été définie, la première devient la miniature
        if thumbnail_count == 0 and listing_photos:
            listing_photos[0].is_thumbnail = True
            
        new_listing.photos = listing_photos
        
        db.session.add(new_listing)
        db.session.commit()
        
        return jsonify(new_listing.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Bad request: {str(e)}"}), 400






#--------------------------------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=True, port=port)
