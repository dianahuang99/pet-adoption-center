"""Organization model tests."""

# run these tests like:
#
#    python -m unittest test_model_orgs.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Organization, SavedOrgs

os.environ['DATABASE_URL'] = "postgresql:///adopt_a_pet_test"

from app import app

db.create_all()

class OrganizationModelTestCase(TestCase):
    """Test organization model."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 12312
        u = User.signup("testing", "testing@test.com", "password")
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_org_model(self):
        """Does basic model work?"""

        o = Organization(id="testid",
                name="testname",
                img_url="testimgurl",
                mission_statement="testmissionstatement")

        db.session.add(o)
        db.session.commit()
        
        new_user_org = SavedOrgs(user_id=self.uid, org_id=o.id)
        db.session.add(new_user_org)
        db.session.commit()

        # User should have 1 saved organization
        self.assertEqual(len(self.u.org_likes), 1)
        self.assertEqual(self.u.org_likes[0].name, "testname")
        

    def test_org_likes(self):
        o1 = Organization(id="testid",
                name="testname",
                img_url="testimgurl",
                mission_statement="testmissionstatement")

        o2 = Organization(id="testid2",
                name="testname2",
                img_url="testimgurl2",
                mission_statement="testmissionstatement2")

        u = User.signup("yetanothertest", "t@email.com", "password")
        uid = 888
        u.id = uid
        db.session.add_all([o1, o2, u])
        db.session.commit()

        u.org_likes.append(o1)
        u.org_likes.append(o2)

        db.session.commit()

        l = SavedOrgs.query.filter(SavedOrgs.user_id == uid).all()
        self.assertEqual(len(l), 2)
        self.assertEqual(l[0].org_id, o1.id)
        self.assertEqual(l[1].org_id, o2.id)

