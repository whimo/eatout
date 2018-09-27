from . import app, db
from flask import jsonify, abort, request
from sqlalchemy import func
from .models import Place, User, Review
from .serial import serialize

@app.route('/p/<int:id>')
def get_place(id):
    place = Place.query.get(id)
    if place is None:
        abort(404)
    return jsonify(serialize(place))

@app.route('/u/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if user is None:
        abort(404)
    return jsonify(serialize(user))

@app.route('/r/<int:id>')
def get_review(id):
    review = Review.query.get(id)
    if review is None:
        abort(404)
    return jsonify(serialize(review))

@app.route('/register', methods=['POST'])
def register():
    json = request.get_json()
    if not json or not all(param in json for param in ['email', 'password', 'tripadvisor_username']):
        abort(400)
    
    if User.query.filter(func.lower(User.email) == json['email'].lower()).first():
        return jsonify({'error': 'email_exists'})
    
    if User.query.filter(func.lower(User.tripadvisor_username) == json['tripadvisor_username'].lower()).first():
        return jsonify({'error': 'tripadvisor_username_exists'})
        
    user = User(email=json['email'], tripadvisor_username=json['tripadvisor_username'])
    user.set_password(json['password'])

    try:
        db.session.add(user)
        db.session.commit()
    except:
        db.session.rollback()
        abort(500)
    
    return jsonify({'status': 'ok'})