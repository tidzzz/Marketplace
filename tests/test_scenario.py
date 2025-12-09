import unittest
import json
import sys
import os

# Ajouter le dossier parent au path pour importer app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from database.models import Category, User

class TestMarketplaceScenario(unittest.TestCase):
    def setUp(self):
        # Configuration de l'application pour les tests
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Base de données en mémoire pour les tests
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Créer un utilisateur admin pour les tests
            admin = User(email='admin@imt.test', password_hash='hash', is_active=True)
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_category_scenario(self):
        """
        Scénario :
        1. Lister les catégories (doit être vide au début)
        2. Créer une catégorie en tant qu'admin
        3. Lister les catégories (doit contenir la nouvelle catégorie)
        4. Tenter de créer une catégorie sans être admin (doit échouer)
        """
        
        # 1. Lister les catégories (vide)
        response = self.app.get('/api/categories')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [])

        # 2. Créer une catégorie (Admin)
        headers = {'X-User-Email': 'admin@imt.test', 'Content-Type': 'application/json'}
        data = {'name': 'Électronique'}
        response = self.app.post('/api/categories', headers=headers, data=json.dumps(data))
        self.assertEqual(response.status_code, 201)
        category_data = json.loads(response.data)
        self.assertEqual(category_data['name'], 'Électronique')

        # 3. Lister les catégories (1 catégorie)
        response = self.app.get('/api/categories')
        self.assertEqual(response.status_code, 200)
        categories = json.loads(response.data)
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]['name'], 'Électronique')

        # 4. Tenter de créer une catégorie (Non Admin / Anonyme)
        # Sans header
        response = self.app.post('/api/categories', data=json.dumps({'name': 'Meubles'}), content_type='application/json')
        self.assertEqual(response.status_code, 403) # Ou 401 selon l'implémentation, ici admin_required renvoie 403

        # Avec mauvais header
        headers_fake = {'X-User-Email': 'user@imt.test', 'Content-Type': 'application/json'}
        response = self.app.post('/api/categories', headers=headers_fake, data=json.dumps({'name': 'Meubles'}))
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
