from .models import User, Place, Review
from shapely import wkb


def serialize(obj):
    if isinstance(obj, User):
        return _serialize_user(obj)
    elif isinstance(obj, Place):
        return _serialize_place(obj)
    elif isinstance(obj, Review):
        return _serialize_review(obj)


def _serialize_user(obj):
    return {
        'id': obj.id,
        'email': obj.email
    }


def _serialize_place(obj):
    point = None
    if obj.location is not None:
        point = wkb.loads(bytes(obj.location.data))

    return {
        'id': obj.id,
        'name': obj.name,
        'address': obj.address,
        'location': (point.y, point.x) if point else None,
        'place_type': obj.place_type,
        'tripadvisor_url': obj.tripadvisor_url,
        'navicontainer': obj.navicontainer,
        'naviaddress': obj.naviaddress,
        'image_url': obj.image_url,
        'rating': obj.rating
    }


def _serialize_review(obj):
    return {
        'id': obj.id,
        'user_id': obj.user_id,
        'place_id': obj.place_id,
        'place': _serialize_place(Place.query.get(obj.place_id)) if obj.place_id else None,
        'rating': obj.rating,
    }
