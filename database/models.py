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

    def __init__(self,
                 id: int,
                 line1: str,
                 line2: str | None,
                 city: str, postal_code: str) -> None:

        if (id>=1 and 1<=len(line1)<=200) and (line2 is None or 0<=len(line2)<=200) and (1<=len(city)<=100) and (1<=len(postal_code)<=20):
            self.id = id
            self.line1 = line1
            self.line2 = line2
            self.city = city
            self.postal_code = postal_code
        else:
            raise ValueError("Adress too long or too short")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "line1": self.line1,
            "line2": self.line2,
            "city": self.city,
            "postal_code": self.postal_code
        }
