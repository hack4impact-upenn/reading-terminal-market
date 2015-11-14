from functools import wraps

from flask import abort
from flask.ext.login import current_user
from .models import Permission


def permissions_required(*permissions):
    """Restrict a view to users with the given permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not any([current_user.can(permission) for permission in permissions]):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return permissions_required(Permission.ADMINISTER)(f)


def vendor_required(f):
    return permissions_required(Permission.VENDOR)(f)


def merchant_required(f):
    return permissions_required(Permission.MERCHANT)(f)


def merchant_or_vendor_required(f):
    return permissions_required(Permission.MERCHANT, Permission.VENDOR)(f)
