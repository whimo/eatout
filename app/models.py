from . import db, bcrypt, login_manager
from flask_login import UserMixin

PLACE_DEFAULT = 0
PLACE_RESTAURANT = 1
PLACE_CAFE = 2
PLACE_BAR = 3


class User(db.Model, UserMixin):
    id =                   db.Column(db.Integer, primary_key=True)
    email =                db.Column(db.String(60), index=True, unique=True)
    password =             db.Column(db.String(60))
    tripadvisor_username = db.Column(db.String(100), index=True, unique=True)

    reviews = db.relationship('Review', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('ascii')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


@login_manager.user_loader
def loader(user_id):
    return User.query.get(int(user_id))


class Place(db.Model):
    id =              db.Column(db.Integer, primary_key=True)
    name =            db.Column(db.Text, index=True)
    place_type =      db.Column(db.SmallInteger)
    tripadvisor_url = db.Column(db.Text)
    navicontainer =   db.Column(db.String(18))
    naviaddress =     db.Column(db.String(18))
    rating =          db.Column(db.SmallInteger)

    reviews = db.relationship('Review', backref='place', lazy='dynamic')


class Review(db.Model):
    id =       db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer, db.ForeignKey('user.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    rating =   db.Column(db.SmallInteger)
    content =  db.Column(db.Text)
