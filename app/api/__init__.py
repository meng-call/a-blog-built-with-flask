# app/api/__init__.py
from flask import Blueprint, g, request


api = Blueprint('api', __name__)


@api.before_request
def before_request():
    """在每次API请求前检查用户是否已确认"""
    from .errors import forbidden
    
    # 排除获取token的端点，允许未确认用户获取token
    if request.endpoint == 'api.get_token':
        return None
    
    # 安全地检查 g.current_user 是否存在
    current_user = getattr(g, 'current_user', None)
    if current_user and not current_user.is_anonymous and not current_user.confirmed:
        return forbidden('Unconfirmed account')


from . import authentication, posts, users, comments, errors
