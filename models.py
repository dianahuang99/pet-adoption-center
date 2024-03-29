"""SQLAlchemy models for Pet Adopter."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model):
    """User in the system."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True,)

    email = db.Column(db.Text, nullable=False, unique=True,)

    username = db.Column(db.Text, nullable=False, unique=True,)

    password = db.Column(db.Text, nullable=False,)

    org_likes = db.relationship("Organization", secondary='org_likes')
    
    animal_likes = db.relationship('Animal', secondary='animal_likes')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")

        user = User(
            username=username, email=email, password=hashed_pwd, 
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user


class SavedOrgs(db.Model):
    """Mapping saved organizations to users."""

    __tablename__ = "org_likes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="cascade"))

    org_id = db.Column(db.Text, db.ForeignKey("organizations.id", ondelete="cascade"))
    
class SavedAnimals(db.Model):
    """Mapping saved animals to users."""

    __tablename__ = "animal_likes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="cascade"))

    animal_id = db.Column(db.Text, db.ForeignKey("animals.id", ondelete="cascade"))   


class Organization(db.Model):
    """An individual organization."""

    __tablename__ = "organizations"

    id = db.Column(db.Text, primary_key=True,)

    name = db.Column(db.Text, nullable=True)

    img_url = db.Column(db.Text, nullable=True)

    mission_statement = db.Column(db.Text, nullable=True)
    
    
class Animal(db.Model):
    """An individual animal."""

    __tablename__ = "animals"

    id = db.Column(db.Text, primary_key=True,)

    name = db.Column(db.Text, nullable=True)

    img_url = db.Column(db.Text, nullable=True)

    description = db.Column(db.Text, nullable=True)

def connect_db(app):
    db.app = app
    db.init_app(app)
