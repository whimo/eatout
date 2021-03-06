from . import app, models, db, recommender, login_manager
from flask import jsonify, abort, request, g
from sqlalchemy import func
from geoalchemy2 import func as geo
from flask_login import current_user, login_user, logout_user, login_required
from .models import Place, User, Review
from .serial import serialize
import requests
from json import dumps
from shapely import wkb


PLACE_TYPES = {'restaurant': models.PLACE_RESTAURANT,
               'bar': models.PLACE_BAR,
               'cafe': models.PLACE_CAFE}

TYPE_IDS = {models.PLACE_RESTAURANT: 4,
            models.PLACE_BAR: 5,
            models.PLACE_CAFE: 6}


@app.before_request
def before_request():
    '''
    Set current request user before every request
    '''
    g.user = current_user


@login_manager.user_loader
def load_user(user_id):
    '''
    Flask-Login user loader
    '''
    return models.User.query.get(int(user_id))


@app.route('/p/<int:id>')
def get_place(id):
    place = Place.query.get(id)
    if place is None:
        abort(404)
    return jsonify(serialize(place))


@app.route('/p/create')
def create_place():
    data = request.get_json()
    if 'name' not in data:
        return jsonify({'error': 'must provide name'})

    location = None
    if 'lat' in data and 'lon' in data:
        location = 'POINT({} {})'.format(data.get('lon'), data.get('lat'))

    place = models.Place(name=data.get('name'),
                         location=location,
                         address=data.get('address'),
                         place_type=PLACE_TYPES.get(data.get('type')),
                         tripadvisor_url=data.get('tripadvisor_url', '').split('/')[-1],
                         navicontainer=data.get('navicontainer'),
                         naviaddress=data.get('naviaddress'))
    db.session.add(place)
    db.session.commit()

    return jsonify({'status': 'ok', 'id': place.id})


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


@app.route('/r')
def get_reviews():
    if not g.user.is_authenticated:
        return jsonify({'error': 'authentication required'})

    reviews = g.user.reviews.order_by(Review.rating.desc().nullslast()).all()
    return jsonify(list(map(serialize, reviews)))


@app.route('/register', methods=['POST'])
def register():
    json = request.get_json()
    if not json or not all(param in json for param in ['email', 'password']):
        return jsonify({'error': 'invalid_json'})

    if User.query.filter(func.lower(User.email) == json['email'].lower()).first():
        return jsonify({'error': 'email_exists'})

    user = User(email=json['email'])
    user.set_password(json['password'])

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'db_commit_failed'})

    return jsonify({'status': 'ok'})


@app.route('/login', methods=['POST'])
def login():
    if g.user.is_authenticated:
        return jsonify({'error': 'user_logged_in'})

    json = request.get_json()
    if not json or not all(param in json for param in ['email', 'password', 'remember_me'])\
            or type(json['remember_me']) != bool:
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
    if g.user.is_authenticated:
        logout_user()
        return jsonify({'status': 'ok'})

    return jsonify({'error': 'user_not_logged_in'})


@app.route('/current_user')
def get_current_user():
    if g.user is None:
        abort(404)

    return serialize(g.user)


@app.route('/recommend')
def recommend():
    if not g.user:
        return jsonify({'error': 'authentication required'})

    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius = float(request.args.get('radius')) * 1000
        if radius > app.config['MAX_SEARCH_RADIUS']:
            radius = None

    except ValueError:
        lat = None
        lon = None
        radius = None

    place_type = PLACE_TYPES.get(request.args.get('type'))

    if lat and lon and radius:
        places = models.Place.query.filter(
            geo.ST_DWithin(models.Place.location, 'POINT({} {})'.format(lon, lat), radius))
    else:
        places = models.Place.query

    if place_type:
        places = places.filter_by(place_type=place_type)
    else:
        places = places

    try:
        suggestions = recommender.recommend(g.user.id, (place.id for place in places))[:20]
    except KeyError:
        return jsonify(list(map(serialize, places.order_by(models.Place.rating.desc().nullslast()).all()[:20])))

    return jsonify(list(map(serialize, Place.query.filter(Place.id.in_(list(map(int, suggestions)))).all())))


@app.route('/rate/<int:id>', methods=['POST'])
def rate_place(id):
    if not g.user:
        return jsonify({'error': 'authentication required'})

    json = request.get_json()
    rating = json['rating']
    if not isinstance(rating, int):
        return jsonify({'error': 'not an int'})

    first_review = False
    if g.user.reviews.count() == 0:
        first_review = True

    review = Review.query.filter_by(user_id=g.user.id, place_id=id).first()
    if not review:
        review = Review(user_id=g.user.id, place_id=id)
        db.session.add(review)
        db.session.commit()

    review.rating = rating
    db.session.commit()

    if first_review:
        recommender.fit()
    else:
        recommender.fit_partial([review])

    return jsonify({'status': 'ok'})


def create_naviaddress(place, default_lang=app.config['NAVIADDRESS_DEFAULT_LANG'], address_type='free'):
    point = None
    if place.location is not None:
        point = wkb.loads(bytes(place.location.data))

    data = {'lat': float(point.y),
            'lon': float(point.x),
            'default_lang': default_lang,
            'address_type': address_type}

    session_url = app.config['NAVIADDRESS_API_URL']
    session_json = {
        'email': app.config['BOT_EMAIL'],
        'password': app.config['BOT_PASSWORD'],
        'type': 'email'
    }
    r = requests.post(session_url, data=dumps(session_json), headers={'Content-Type': 'application/json'})

    if not r.ok:
        return jsonify({'error': 'naviaddress_session_error'})

    session_response_json = r.json()

    if session_response_json and 'token' in session_response_json:
        token = session_response_json['token']
    else:
        return jsonify({'error': 'naviaddress_session_json_error'})

    auth_headers = {'Content-Type': 'application/json',
                    'Accept': 'appication/json',
                    'auth-token': token}

    r = requests.post(app.config['NAVIADDRESS_ADDRESSES_URL'], data=data,
                      headers=auth_headers)
    if not r.ok:
        return jsonify({'error': 'naviaddress_creation_error'})

    creation_response_json = r.json()
    container = creation_response_json.get('container')
    naviaddress = creation_response_json.get('naviaddress')

    r = requests.post(app.config['NAVIADDRESS_ACCEPT_URL'].format(container, naviaddress),
                      data={'container': container, 'naviaddress': naviaddress},
                      headers=auth_headers)
    if not r.ok:
        return jsonify({'error': 'naviaddress_accept_error'})

    info = {'name': place.name,
            'map_visibility': 'true',
            'category': TYPE_IDS.get(place.place_type),
            'postal_address': place.address
            }

    r = requests.put(app.config['NAVIADDRESS_UPDATE_URL'].format(container, naviaddress),
                     data=info,
                     headers=auth_headers)

    if r.json():
        return jsonify({
            'status': 'ok',
            'response': r.json()
        })

    return jsonify({'error': 'naviaddress_creation_json_error'})
