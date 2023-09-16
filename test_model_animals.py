"""Animal model tests."""

# run these tests like:
#
#    python -m unittest test_model_animals.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Animal, SavedAnimals

os.environ['DATABASE_URL'] = "postgresql:///adopt_a_pet_test"

from app import app

db.create_all()

class AnimalModelTestCase(TestCase):
    """Test animal model."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 1121
        u = User.signup("testing", "testing@test.com", "password")
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""

        a = Animal(id='testid',
                name='testname',
                img_url='testurl',
                description='testdescription',)

        db.session.add(a)
        db.session.commit()
        
        new_user_animal = SavedAnimals(user_id=self.uid, animal_id=a.id)
        db.session.add(new_user_animal)
        db.session.commit()

        # User should have 1 liked animal
        self.assertEqual(len(self.u.animal_likes), 1)
        self.assertEqual(self.u.animal_likes[0].name, "testname")
        

    def test_animal_likes(self):
        a1 = Animal(id='testid',
                name='testname',
                img_url='testurl',
                description='testdescription',)

        a2 = Animal(id='testid2',
                name='testname2',
                img_url='testurl2',
                description='testdescription2',)

        u = User.signup("testuser", "test@email.com", "password")
        uid = 23421
        u.id = uid
        db.session.add_all([a1, a2, u])
        db.session.commit()

        u.animal_likes.append(a1)
        u.animal_likes.append(a2)

        db.session.commit()

        l = SavedAnimals.query.filter(SavedAnimals.user_id == uid).all()
        self.assertEqual(len(l), 2)
        self.assertEqual(l[0].animal_id, a1.id)
        self.assertEqual(l[1].animal_id, a2.id)

