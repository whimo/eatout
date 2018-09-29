from .models import User, Place, Review


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
        'email': obj.email,
        'tripadvisor_username': obj.tripadvisor_username
    }


def _serialize_place(obj):
    return {
        'id': obj.id,
        'name': obj.name,
        'place_type': obj.place_type,
        'tripadvisor_url': obj.tripadvisor_url,
        'navicontainer': obj.navicontainer,
        'naviaddress': obj.naviaddress,
        'rating': obj.rating
    }


def _serialize_review(obj):
    return {
        'id': obj.id,
        'user_id': obj.user_id,
        'place_id': obj.place_id,
        'rating': obj.rating,
        'content': obj.content
    }
