"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views_animals.py


import os
from unittest import TestCase

from models import db, connect_db, Animal, User, SavedAnimals
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///adopt_a_pet_test"

from app import app, CURR_USER_KEY

db.create_all()

app.config["WTF_CSRF_ENABLED"] = False

class AnimalViewTestCase(TestCase):
    """Test views for animals."""

    def setUp(self):
        """Create test client."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        
        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser"
        )
        self.testuser_id = 1121
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_unauthorized_animals_search(self):
        with self.client as c:
            resp = c.get("/animals/1", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login first!", str(resp.data))
            
            resp = c.get("/animals/1?type=Dog", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login first!", str(resp.data))

            resp = c.get("/animals/1?gender=female", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login first!", str(resp.data))
                        
            resp = c.get("/animals/1?name=test", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login first!", str(resp.data))

    def test_authorized_animals_search(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get("/animals/1")
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', str(resp.data))
            
            resp = c.get("/animals/1?type=Dog")
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', str(resp.data))
            
            resp = c.get("/animals/1?gender=female", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', str(resp.data))
            
            resp = c.get("/animals/1?name=test", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            resp = c.get("/animals/1?name=dfaasdfasdfadsf", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sorry, no animals found', str(resp.data))

    def setup_animal_likes(self):
        a1 = Animal(id='testid',
                name='testname',
                img_url='testurl',
                description='testdescription',)
        a2 = Animal(id='testid2',
                name='testname2',
                img_url='testurl2',
                description='testdescription2',)
        a3 = Animal(id='testid3',
                name='alreadyLikedAnimal',
                img_url='testurl3',
                description='testdescription3',)
        db.session.add_all([a1, a2, a3])
        db.session.commit()

        l1 = SavedAnimals(user_id=self.testuser_id, animal_id='testid3')

        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        self.setup_animal_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), "html.parser")
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 2)

            # test for a count of 0 saved organizations
            self.assertIn("0", found[0].text)

            # Test for a count of 1 saved animals
            self.assertIn("1", found[1].text)

    def test_add_animal_like(self):
        self.setup_animal_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/animal/save/testid2", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            # to check if the current added animal worked
            animal_likes = SavedAnimals.query.filter(SavedAnimals.animal_id == 'testid2').all()
            self.assertEqual(len(animal_likes), 1)
            self.assertEqual(animal_likes[0].user_id, self.testuser_id)
            
            # to check if it was added to the previous manually added animal in line 132
            animal_likes_all = SavedAnimals.query.filter(SavedAnimals.user_id == self.testuser_id).all()
            self.assertEqual(len(animal_likes_all), 2)

    def test_remove_animal_like(self):
        self.setup_animal_likes()
        
        # to check if there is currently one animal saved from the setup
        a = Animal.query.filter(Animal.name == "alreadyLikedAnimal").one()
        self.assertIsNotNone(a)

        s = SavedAnimals.query.filter(
            SavedAnimals.user_id == self.testuser_id and SavedAnimals.animal_id == a.id
        ).one()
        #########

        self.assertIsNotNone(s)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
                
            resp = c.post(f"/animal/save/{a.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            animal_likes = SavedAnimals.query.filter(SavedAnimals.animal_id == a.id).all()
            # the like has been deleted
            self.assertEqual(len(animal_likes), 0)

    def test_unauthenticated_like(self):
        self.setup_animal_likes()

        a = Animal.query.filter(Animal.name == "alreadyLikedAnimal").one()
        self.assertIsNotNone(a)

        save_count = SavedAnimals.query.count()

        with self.client as c:
            resp = c.post(f"/animal/save/{a.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Please login first!", str(resp.data))

            # The number of saved animals has not changed since making the request
            self.assertEqual(save_count, SavedAnimals.query.count())
            
    