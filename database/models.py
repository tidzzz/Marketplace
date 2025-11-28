from sqlalchemy.orm import validates
from database.database import db

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
