from . import app, db
from flask import jsonify, abort, request
from sqlalchemy import func
from flask_login import current_user, login_user, logout_user, login_required
from .models import Place, User, Review
from .serial import serialize

@app.route('/p/<int:id>')
def get_place(id):
    place = Place.query.get(id)
    if place is None:
        abort(404)
    return jsonify(serialize(place))

@app.route('/p/search/<string:name>')
def find_place(name):
    places = Place.query.filter(Place.name.ilike('%' + name + '%')).all()
    if len(places) < 1:
        abort(404)

    return jsonify([serialize(place) for place in places])

@app.route('/p/range/<int:start>/<int:stop>/<string:name>')
def find_place_range(start, stop, name):
    places = Place.query.filter(Place.name.ilike('%' + name + '%')).all()
    if len(places) < 1:
        abort(404)

    return jsonify([serialize(place) for place in places][start:stop])

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
        return jsonify({'error': 'invalid_json'})

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
        return jsonify({'error': 'db_commit_failed'})

    return jsonify({'status': 'ok'})

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'error': 'user_logged_in'})

    json = request.get_json()
    if not json or not all(param in json for param in ['email', 'password', 'remember_me']) or type(json['remember_me']) != bool:
        return jsonify({'error': 'invalid_json'})

    user = User.query.filter(func.lower(User.email) == json['email'].lower()).first()
    if user is None:
        return jsonify({'error': 'no_user'})
    elif not user.check_password(json['password']):
        return jsonify({'error': 'wrong_password'})

    login_user(user, json['remember_me'])
    return jsonify({'status': 'ok'})

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        return jsonify({'status': 'ok'})

    return jsonify({'error': 'user_not_logged_in'})

@app.route('/current_user')
def get_current_user():
    if current_user is None:
        abort(404)

    return serialize(current_user)

@app.route('/demo')
def demo():
    places = Place.query.all()
    return jsonify(list(reversed(list(map(serialize, places)))))
