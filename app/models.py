from . import db

PLACE_DEFAULT = 0
PLACE_RESTAURANT = 1
PLACE_CAFE = 2
PLACE_BAR = 3


class User(db.Model):
    id =                   db.Column(db.Integer, primary_key=True)
    email =                db.Column(db.String(60), index=True)
    password =             db.Column(db.String(60))
    tripadvisor_username = db.Column(db.String(100), index=True)

    reviews = db.relationship('Review', backref='user', lazy='dynamic')


class Place(db.Model):
    id =             db.Column(db.Integer, primary_key=True)
    name =           db.Column(db.Text, index=True)
    place_type =     db.Column(db.SmallInteger)
    tripadvisor_id = db.Column(db.Integer)
    navicontainer =  db.Column(db.String(18))
    naviaddress =    db.Column(db.String(18))
    rating =         db.Column(db.SmallInteger)

    reviews = db.relationship('Review', backref='place', lazy='dynamic')


class Review(db.Model):
    id =       db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer, db.ForeignKey('user.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    rating =   db.Column(db.SmallInteger)
    content =  db.Column(db.Text)
