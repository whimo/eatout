from . import db, bcrypt, login_manager
from flask_login import UserMixin
from geoalchemy2.types import Geography

PLACE_DEFAULT = 0
PLACE_RESTAURANT = 1
PLACE_CAFE = 2
PLACE_BAR = 3


class User(db.Model, UserMixin):
    id =              db.Column(db.Integer, primary_key=True)
    email =           db.Column(db.String(60), index=True, unique=True)
    password =        db.Column(db.String(60))
    tripadvisor_uid = db.Column(db.String(100), index=True, unique=True)

    reviews = db.relationship('Review', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('ascii')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % self.id


class Place(db.Model):
    id =              db.Column(db.Integer, primary_key=True)
    name =            db.Column(db.Text, index=True)
    location =        db.Column(Geography('POINT'))
    address =         db.Column(db.Text)
    place_type =      db.Column(db.SmallInteger)
    tripadvisor_url = db.Column(db.Text)
    image_url =       db.Column(db.Text)
    navicontainer =   db.Column(db.String(18))
    naviaddress =     db.Column(db.String(18))
    rating =          db.Column(db.SmallInteger)

    reviews = db.relationship('Review', backref='place', lazy='dynamic')


class Review(db.Model):
    id =       db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer, db.ForeignKey('user.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    rating =   db.Column(db.SmallInteger)
    title =    db.Column(db.Text)
    content =  db.Column(db.Text)
