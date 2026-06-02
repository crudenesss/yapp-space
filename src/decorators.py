"""Decorators used within application"""

from functools import wraps
from flask import abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import UserService


def privilege_required(f):
    """Forbid access for users with no privileges for resource"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user = UserService().get_user_by_id(get_jwt_identity())
        if not user.is_privileged():
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function
