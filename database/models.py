from sqlalchemy.orm import validates
from database.database import db
from datetime import datetime, timezone

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
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    
    def __repr__(self):
        return f'<User {self.email}>'
    

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id
        }

    def __repr__(self):
        return f'<Category {self.name}>'

class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    line1 = db.Column(db.String(200), nullable=False)
    line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)

    user_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    @validates('line1')
    def validate_line1(self, key, value):
        if not value or len(value.strip()) < 1:
            raise ValueError("line1 must be at least 1 character")
        if len(value) > 200:
            raise ValueError("line1 must be at most 200 characters")
        return value
    
    @validates('city')
    def validate_city(self, key, value):
        if not value or len(value.strip()) < 1:
            raise ValueError("city must be at least 1 character")
        if len(value) > 100:
            raise ValueError("city must be at most 100 characters")
        return value
    
    @validates('postal_code')
    def validate_postal_code(self, key, value):
        if not value or len(value.strip()) < 1:
            raise ValueError("postal_code must be at least 1 character")
        if len(value) > 20:
            raise ValueError("postal_code must be at most 20 characters")
        return value
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "line1": self.line1,
            "line2": self.line2,
            "city": self.city,
            "postal_code": self.postal_code
        }
    
    def __repr__(self):
        return f'<Address {self.id}: {self.line1}, {self.city}>'

class Listing(db.Model):
    __tablename__ = 'listings'

    id = db.Column(db.Integer, primary_key=True)
    seller_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.String(5000), nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    shipping_cents = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active') # active, sold, deleted
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    photos = db.relationship('ListingPhoto', backref='listing', lazy=True, cascade="all, delete-orphan")

    @validates('title')
    def validate_title(self, key, value):
        if not value or len(value.strip()) < 1:
            raise ValueError("title must be at least 1 character")
        if len(value) > 140:
            raise ValueError("title must be at most 140 characters")
        return value

    @validates('description')
    def validate_description(self, key, value):
        if not value or len(value.strip()) < 1:
            raise ValueError("description must be at least 1 character")
        if len(value) > 5000:
            raise ValueError("description must be at most 5000 characters")
        return value
    
    @validates('price_cents')
    def validate_price_cents(self, key, value):
        if value < 0:
            raise ValueError("price_cents must be non-negative")
        return value

    @validates('shipping_cents')
    def validate_shipping_cents(self, key, value):
        if value < 0:
            raise ValueError("shipping_cents must be non-negative")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "seller_email": self.seller_email,
            "title": self.title,
            "description": self.description,
            "price_cents": self.price_cents,
            "shipping_cents": self.shipping_cents,
            "category_id": self.category_id,
            "status": self.status,
            "photos": [photo.to_dict() for photo in self.photos],
            "created_at": self.created_at.isoformat().replace('+00:00', 'Z')
        }

class ListingPhoto(db.Model):
    __tablename__ = 'listing_photos'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    is_thumbnail = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "url": self.url,
            "is_thumbnail": self.is_thumbnail
        }

class BuyerProtection(db.Model):
    __tablename__ = 'buyer_protection'

    id = db.Column(db.Integer, primary_key=True)
    ratio_percent = db.Column(db.Float, nullable=False, default=0.0)
    bias_cents = db.Column(db.Integer, nullable=False, default=0)

    @validates('ratio_percent')
    def validate_ratio_percent(self, key, value):
        if value < 0:
            raise ValueError("ratio_percent must be non-negative")
        return value

    @validates('bias_cents')
    def validate_bias_cents(self, key, value):
        if value < 0:
            raise ValueError("bias_cents must be non-negative")
        return value

    def to_dict(self):
        return {
            "ratio_percent": self.ratio_percent,
            "bias_cents": self.bias_cents
        }
        
class CreditTxn(db.Model):
    __tablename__ = 'credit_txns'

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    
    # Type de transaction : 'topup' (rechargement), 'purchase' (achat), 'sale_payout' (vente), 'refund' (remboursement)
    txn_type = db.Column(db.String(50), nullable=False)
    
    # Montant de la transaction (positif ou négatif selon la logique métier)
    amount_cents = db.Column(db.Integer, nullable=False)
    
    # Solde de l'utilisateur APRÈS la transaction 
    balance_after_cents = db.Column(db.Integer, nullable=False)
    
    # ID de l'achat lié (Optionnel, car un 'topup' n'est lié à aucun achat)
    related_purchase_id = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.txn_type,
            "amount_cents": self.amount_cents,
            "balance_after_cents": self.balance_after_cents,
            "related_purchase_id": self.related_purchase_id,
            "created_at": self.created_at.isoformat().replace('+00:00', 'Z')
        }

class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    buyer_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    seller_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    
    item_price_cents = db.Column(db.Integer, nullable=False)
    shipping_cents = db.Column(db.Integer, nullable=False)
    insurance_part_cents = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    
    # Address snapshot
    address_id = db.Column(db.Integer, nullable=True) # Original address ID
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200), nullable=True)
    address_city = db.Column(db.String(100), nullable=False)
    address_postal_code = db.Column(db.String(20), nullable=False)
    
    status = db.Column(db.String(20), nullable=False, default='paid') # paid, delivered, closed, refunded
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "buyer_email": self.buyer_email,
            "seller_email": self.seller_email,
            "item_price_cents": self.item_price_cents,
            "shipping_cents": self.shipping_cents,
            "insurance_part_cents": self.insurance_part_cents,
            "total_cents": self.total_cents,
            "address": {
                "id": self.address_id if self.address_id else 0,
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.address_city,
                "postal_code": self.address_postal_code
            },
            "status": self.status,
            "created_at": self.created_at.isoformat().replace('+00:00', 'Z')
        }
