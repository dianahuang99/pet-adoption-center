"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views_orgs.py


import os
from unittest import TestCase

from models import db, connect_db, Organization, User, SavedOrgs
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///adopt_a_pet_test"

from app import app, CURR_USER_KEY

db.create_all()

app.config["WTF_CSRF_ENABLED"] = False

class OrganizationViewTestCase(TestCase):
    """Test views for organizations."""

    def setUp(self):
        """Create test client."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        
        self.testuser = User.signup(
            username="testuser1",
            email="test@test.com",
            password="testuser"
        )
        self.testuser_id = 1122
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_unauthorized_organizations_search(self):
        with self.client as c:
            resp = c.get("/organizations/1", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login first!", str(resp.data))
            
            resp = c.get("/organizations/1?state=AZ", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login first!", str(resp.data))

            resp = c.get("/organizations/1?location=11355", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Please login first!", str(resp.data))

    def test_authorized_organizations_search(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get("/organizations/1")
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', str(resp.data))
            
            resp = c.get("/organizations/1?state=AZ", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', str(resp.data))
            
            resp = c.get("/organizations/1?location=11355", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', str(resp.data))
            
            resp = c.get("/organizations/1?location=dfaasdfasdfadsf", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('no organizations found', str(resp.data))

    def setup_org_likes(self):
        o1 = Organization(id="testid",
                name="testname",
                img_url="testimgurl",
                mission_statement="testmissionstatement")
        o2 = Organization(id="testid2",
                name="testname2",
                img_url="testimgurl2",
                mission_statement="testmissionstatement2")
        o3 = Organization(id="testid3",
                name="alreadyLikedOrg",
                img_url="testimgurl3",
                mission_statement="testmissionstatement3")
        db.session.add_all([o1, o2, o3])
        db.session.commit()

        l1 = SavedOrgs(user_id=self.testuser_id, org_id='testid3')

        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        self.setup_org_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), "html.parser")
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 2)

            # test for a count of 1 saved organizations
            self.assertIn("1", found[0].text)

            # Test for a count of 0 saved animals
            self.assertIn("0", found[1].text)

    def test_add_org_like(self):
        self.setup_org_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/organization/save/testid2", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            # to check if the current added animal worked
            org_likes = SavedOrgs.query.filter(SavedOrgs.org_id == 'testid2').all()
            self.assertEqual(len(org_likes), 1)
            self.assertEqual(org_likes[0].user_id, self.testuser_id)
            
            # to check if it was added to the previous manually added animal in line 132
            org_likes_all = SavedOrgs.query.filter(SavedOrgs.user_id == self.testuser_id).all()
            self.assertEqual(len(org_likes_all), 2)

    def test_remove_org_like(self):
        self.setup_org_likes()
        
        # to check if there is currently one animal saved from the setup
        o = Organization.query.filter(Organization.name == "alreadyLikedOrg").one()
        self.assertIsNotNone(o)

        s = SavedOrgs.query.filter(
            SavedOrgs.user_id == self.testuser_id and SavedOrgs.org_id == o.id
        ).one()
        #########

        self.assertIsNotNone(s)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
                
            resp = c.post(f"/organization/save/{o.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            org_likes = SavedOrgs.query.filter(SavedOrgs.org_id == o.id).all()
            # the like has been deleted
            self.assertEqual(len(org_likes), 0)

    def test_unauthenticated_like(self):
        self.setup_org_likes()

        o = Organization.query.filter(Organization.name == "alreadyLikedOrg").one()
        self.assertIsNotNone(o)

        save_count = SavedOrgs.query.count()

        with self.client as c:
            resp = c.post(f"/organization/save/{o.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Please login first!", str(resp.data))

            # The number of saved organizations has not changed since making the request
            self.assertEqual(save_count, SavedOrgs.query.count())