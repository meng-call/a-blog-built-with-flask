from functools import wraps
from flask import g
from .errors import forbidden
from ..models import Permission


def permission_required(permission):
    """API 权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user or not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """API 管理员权限检查装饰器"""
    return permission_required(Permission.ADMIN)(f)
