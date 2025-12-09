from functools import wraps
import os
import uuid
from flask import Flask, jsonify, request, render_template, make_response, send_from_directory #, url_for, redirect
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


# Configuration de l'upload
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'instance', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5 MiB

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Payload too large: max 5 MiB"}), 413


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
        if not user or not user.is_active:
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

@app.route('/api/users/<string:email>', methods=['DELETE'])
@admin_required
def delete_user(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Not found"}), 404
        
    user.is_active = False
    
    # Suppression de toutes ses annonces actives
    listings = Listing.query.filter_by(seller_email=email, status='active').all()
    for listing in listings:
        listing.status = 'deleted'
        
    db.session.commit()
    
    return '', 204 


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

@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({"error": "Not found"}), 404
    
    # Si l'annonce est active, elle est publique
    if listing.status == 'active':
        return jsonify(listing.to_dict()), 200
        
    # Si l'annonce n'est pas active (sold ou deleted), vérification des droits
    user_email = request.headers.get('X-User-Email')
    
    # Admin peut tout voir
    if user_email == 'admin@imt.test':
        return jsonify(listing.to_dict()), 200
        
    # Le vendeur peut voir ses propres annonces (même sold ou deleted)
    if user_email and user_email == listing.seller_email:
        return jsonify(listing.to_dict()), 200
        
    # Sinon, on cache l'annonce (404 pour deleted, et aussi pour sold selon la spec stricte)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/listings/<int:listing_id>', methods=['PUT'])
@authenticated_required
def update_listing(user, listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({"error": "Not found"}), 404
        
    # Vérifier que l'utilisateur est le vendeur ou admin
    if listing.seller_email != user.email and user.email != 'admin@imt.test':
        return jsonify({"error": "Forbidden: not owner"}), 403
        
    # Vérifier que l'annonce est active
    if listing.status != 'active':
        return jsonify({"error": "Bad request: listing not active"}), 400
        
    data = request.get_json()
    
    
    required_fields = ['title', 'description', 'price_cents', 'shipping_cents', 'category_id', 'photos']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Bad request: missing {field}"}), 400
            
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({"error": "Bad request: invalid category_id"}), 400

      
        
    photos_data = data['photos']
    if not isinstance(photos_data, list) or len(photos_data) < 1:
        return jsonify({"error": "Bad request: photos must be a non-empty list"}), 400
    if len(photos_data) > 12:
         return jsonify({"error": "Bad request: too many photos (max 12)"}), 400

    try:
        
        listing.title = data['title']
        listing.description = data['description']
        listing.price_cents = data['price_cents']
        listing.shipping_cents = data['shipping_cents']
        listing.category_id = data['category_id']
        
        # Remplacement complet des photos
        # On supprime les anciennes photos 
        ListingPhoto.query.filter_by(listing_id=listing.id).delete()
        
        # Gestion des nouvelles photos
        thumbnail_count = sum(1 for p in photos_data if p.get('is_thumbnail', False))
        if thumbnail_count > 1:
             return jsonify({"error": "Bad request: at most one photo can be a thumbnail"}), 400
        
        listing_photos = []
        for photo_data in photos_data:
            if 'url' not in photo_data:
                 return jsonify({"error": "Bad request: photo missing url"}), 400
            
            is_thumbnail = photo_data.get('is_thumbnail', False)
            listing_photos.append(ListingPhoto(listing_id=listing.id, url=photo_data['url'], is_thumbnail=is_thumbnail))
            
        # Si aucune miniature n'a été définie, la première devient la miniature
        if thumbnail_count == 0 and listing_photos:
            listing_photos[0].is_thumbnail = True
            
        listing.photos = listing_photos
        
        db.session.commit()
        
        return jsonify(listing.to_dict()), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Bad request: {str(e)}"}), 400
    
@app.route('/api/listings/<int:listing_id>', methods=['DELETE'])
@authenticated_required
def delete_listing(user, listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({"error": "Not found"}), 404
        
    # Vérifier que l'utilisateur est le vendeur ou admin
    if listing.seller_email != user.email and user.email != 'admin@imt.test':
        return jsonify({"error": "Forbidden: not owner"}), 403
        
    # Si l'annonce est déjà vendue, le vendeur ne peut pas la supprimer
    if listing.status == 'sold' and user.email != 'admin@imt.test':
        return jsonify({"error": "Forbidden: cannot delete sold listing"}), 403
        
    listing.status = 'deleted'
    db.session.commit()
    
    return '', 204 

#-------------------------CREDITS--------------------------#

#-------------------------CONFIG--------------------------#

@app.route('/api/config/buyer-protection', methods=['GET'])
def get_buyer_protection():
    config = BuyerProtection.query.first()
    if not config:
        return jsonify({"ratio_percent": 0.0, "bias_cents": 0}), 200
    return jsonify(config.to_dict()), 200

@app.route('/api/config/buyer-protection', methods=['PUT'])
@admin_required
def update_buyer_protection():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Bad request: missing data"}), 400
        
    if 'ratio_percent' not in data or 'bias_cents' not in data:
        return jsonify({"error": "Bad request: missing required fields"}), 400
        
    config = BuyerProtection.query.first()
    if not config:
        config = BuyerProtection()
        db.session.add(config)
    
    try:
        config.ratio_percent = float(data['ratio_percent'])
        config.bias_cents = int(data['bias_cents'])
        db.session.commit()
        return jsonify(config.to_dict()), 200
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Bad request: {str(e)}"}), 400

#------------------------------------BROWSE-----------------------------------#
def calculate_insurance_and_total(price_cents, shipping_cents, config):
    if not config:
        ratio = Decimal(0)
        bias = 0
    else:
        ratio = Decimal(str(config.ratio_percent))
        bias = config.bias_cents
    
    price = Decimal(price_cents)
    # percent_part = round_half_up(P * r / 100)
    percent_part = (price * ratio / Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    insurance_part_cents = int(percent_part) + bias
    total_cents = price_cents + shipping_cents + insurance_part_cents
    return insurance_part_cents, total_cents

@app.route('/api/browse/listings', methods=['GET'])
def browse_listings():
    # Parameters
    q = request.args.get('q')
    category_id = request.args.get('category_id', type=int)
    min_price = request.args.get('min_price_cents', type=int)
    max_price = request.args.get('max_price_cents', type=int)
    min_total = request.args.get('min_total_cents', type=int)
    max_total = request.args.get('max_total_cents', type=int)
    sort_by = request.args.get('sort')
    order = request.args.get('order', default='asc')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=20, type=int)
    if page_size > 50: page_size = 50
    
    # Config
    config = BuyerProtection.query.first()
    
    # Base Query
    query = Listing.query.filter_by(status='active')
    
    # Filter: q (Title OR Description)
    if q:
        search = f"%{q}%"
        query = query.filter(or_(Listing.title.ilike(search), Listing.description.ilike(search)))
        
    # Filter: category_id (and descendants)
    if category_id:
        # Get all categories to build tree
        all_cats = Category.query.all()
        # Build adjacency list
        children = {}
        for c in all_cats:
            if c.parent_id:
                children.setdefault(c.parent_id, []).append(c.id)
        
        # BFS to find all descendants
        descendants = {category_id}
        queue = [category_id]
        while queue:
            curr = queue.pop(0)
            if curr in children:
                for child_id in children[curr]:
                    descendants.add(child_id)
                    queue.append(child_id)
        
        query = query.filter(Listing.category_id.in_(descendants))

    # Filter: price
    if min_price is not None:
        query = query.filter(Listing.price_cents >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price_cents <= max_price)
        
    # Fetch all candidates
    listings = query.all()
    
    # Compute totals and enrich
    results = []
    for l in listings:
        insurance, total = calculate_insurance_and_total(l.price_cents, l.shipping_cents, config)
        
        # Filter: total
        if min_total is not None and total < min_total:
            continue
        if max_total is not None and total > max_total:
            continue
            
        l_dict = l.to_dict()
        l_dict['insurance_part_cents'] = insurance
        l_dict['total_cents'] = total
        results.append(l_dict)
        
    # Sort
    reverse = (order == 'desc')
    if sort_by == 'total':
        results.sort(key=lambda x: (x['total_cents'], x['id']), reverse=reverse)
    elif sort_by == 'price':
        results.sort(key=lambda x: (x['price_cents'], x['id']), reverse=reverse)
    else:
        # Default sort (ties broken by id ASC)
        # We'll sort by ID as a stable default.
        results.sort(key=lambda x: x['id'], reverse=reverse)

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated = results[start:end]
    
    return jsonify(paginated), 200

#------------------------------------PURCHASES-----------------------------------------#

@app.route('/api/purchases', methods=['GET'])
@authenticated_required
def list_purchases(user):
    role = request.args.get('role', default='buyer')
    
    if role == 'seller':
        purchases = Purchase.query.filter_by(seller_email=user.email).all()
    else:
        purchases = Purchase.query.filter_by(buyer_email=user.email).all()
        
    return jsonify([p.to_dict() for p in purchases]), 200

@app.route('/api/purchases', methods=['POST'])
@authenticated_required
def create_purchase(user):
    data = request.get_json()
    if not data or 'listing_id' not in data or 'address_id' not in data:
        return jsonify({"error": "Bad request: missing fields"}), 400
        
    listing = Listing.query.get(data['listing_id'])
    address = Address.query.get(data['address_id'])
    
    if not listing:
        return jsonify({"error": "Not found: listing"}), 404
    if not address:
        return jsonify({"error": "Not found: address"}), 404
        
    # Preconditions
    if listing.seller_email == user.email:
        return jsonify({"error": "Forbidden: cannot buy own listing"}), 403
    if listing.status != 'active':
        return jsonify({"error": "Bad request: listing not active"}), 400
    if address.user_email != user.email:
        return jsonify({"error": "Forbidden: address not owned"}), 403
        
    # Calcul des montants
    config = BuyerProtection.query.first()
    insurance, total = calculate_insurance_and_total(listing.price_cents, listing.shipping_cents, config)
    
    if user.credits_cents < total:
        return jsonify({"error": "Bad request: insufficient credits"}), 400
        
    try:
        # 1. Débit acheteur
        user.credits_cents -= total
        buyer_txn = CreditTxn(
            user_email=user.email,
            type='purchase',
            amount_cents=-total,
            balance_after_cents=user.credits_cents
        )
        db.session.add(buyer_txn)
        
        # 2. Crédit vendeur
        seller = User.query.filter_by(email=listing.seller_email).first()
        payout = listing.price_cents + listing.shipping_cents
        seller.credits_cents += payout
        seller_txn = CreditTxn(
            user_email=seller.email,
            type='sale_payout',
            amount_cents=payout,
            balance_after_cents=seller.credits_cents
        )
        db.session.add(seller_txn)
        
        # 3. Création Purchase
        purchase = Purchase(
            buyer_email=user.email,
            seller_email=listing.seller_email,
            listing_id=listing.id,
            item_price_cents=listing.price_cents,
            shipping_cents=listing.shipping_cents,
            insurance_part_cents=insurance,
            total_cents=total,
            address_line1=address.line1,
            address_line2=address.line2,
            address_city=address.city,
            address_postal_code=address.postal_code
        )
        db.session.add(purchase)
        
        # 4. Mise à jour Listing
        listing.status = 'sold'
        
        # Commit intermédiaire pour avoir l'ID du purchase
        db.session.flush()
        
        # Lier les transactions au purchase
        buyer_txn.related_purchase_id = purchase.id
        seller_txn.related_purchase_id = purchase.id
        
        db.session.commit()
        return jsonify(purchase.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/api/purchases/<int:purchase_id>', methods=['GET'])
@authenticated_required
def get_purchase(user, purchase_id):
    purchase = Purchase.query.get(purchase_id)
    if not purchase:
        return jsonify({"error": "Not found"}), 404
        
    # Vérification des droits (acheteur, vendeur ou admin)
    if user.email != purchase.buyer_email and \
       user.email != purchase.seller_email and \
       user.email != 'admin@imt.test':
        return jsonify({"error": "Forbidden"}), 403
        
    return jsonify(purchase.to_dict()), 200

@app.route('/api/purchases/<int:purchase_id>/declare', methods=['POST'])
@authenticated_required
def declare_purchase(user, purchase_id):
    purchase = Purchase.query.get(purchase_id)
    if not purchase:
        return jsonify({"error": "Not found"}), 404
        
    # Seul l'acheteur peut déclarer
    if user.email != purchase.buyer_email:
        return jsonify({"error": "Forbidden: buyer only"}), 403
        
    # Vérifier l'état
    if purchase.status != 'paid': # 'delivered' n'est pas utilisé dans le flow simplifié mais mentionné dans la spec
        return jsonify({"error": "Conflict: purchase is already terminal"}), 409
        
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Bad request: missing status"}), 400
        
    new_status = data['status']
    if new_status not in ['OK', 'NOT_RECEIVED', 'NOT_AS_DESCRIBED']:
        return jsonify({"error": "Bad request: invalid status"}), 400
        
    try:
        if new_status == 'OK':
            purchase.status = 'closed'
        else:
            # Remboursement (item + shipping, pas l'assurance)
            refund_amount = purchase.item_price_cents + purchase.shipping_cents
            user.credits_cents += refund_amount
            
            refund_txn = CreditTxn(
                user_email=user.email,
                type='refund',
                amount_cents=refund_amount,
                balance_after_cents=user.credits_cents,
                related_purchase_id=purchase.id
            )
            db.session.add(refund_txn)
            purchase.status = 'refunded'
            
        db.session.commit()
        return '', 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal error: {str(e)}"}), 500
    

#-------------------------------------PHOTOS-----------------------------------------------#

@app.route('/api/photos', methods=['POST'])
@authenticated_required
def upload_photo(user):
    if 'file' not in request.files:
        return jsonify({"error": "Bad request: missing form field 'file'"}), 400
        
    file = request.files['file']
    
    if not file or file.filename == '':
        return jsonify({"error": "Bad request: no selected file"}), 400
        
    if file.mimetype not in ['image/jpeg', 'image/png', 'image/webp']:
        return jsonify({"error": "Unsupported media type: only JPEG, PNG, WEBP"}), 415
        
    # Générer un nom de fichier unique
    ext = 'jpg'
    if file.mimetype == 'image/png': ext = 'png'
    elif file.mimetype == 'image/webp': ext = 'webp'
    
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    # Construire l'URL absolue
    url = request.host_url.rstrip('/') + f"/api/photos/{filename}"
    
    response = jsonify({
        "url": url,
        "mime_type": file.mimetype
    })
    response.headers['Location'] = url
    return response, 201

@app.route('/api/photos/<path:photo_id>', methods=['GET'])
def get_photo(photo_id):
    return send_from_directory(UPLOAD_FOLDER, photo_id)

#--------------------------------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=True, port=port)

