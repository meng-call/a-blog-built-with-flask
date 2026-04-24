from flask import g
from flask_httpauth import HTTPBasicAuth
from ..models import User
from .errors import unauthorized

basic_auth = HTTPBasicAuth()


@basic_auth.verify_password
def verify_password(email_or_token, password):
    """验证用户名和密码或token
    
    支持两种认证方式：
    1. 邮箱 + 密码：email_or_token=邮箱, password=密码
    2. Token认证：email_or_token=token, password=''（空字符串）
    """
    # 如果邮箱或token为空，认证失败
    if not email_or_token:
        return False
    
    # 如果密码为空，尝试使用token认证
    if not password:
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    
    # 否则使用邮箱+密码认证
    user = User.query.filter_by(email=email_or_token).first()
    if not user or not user.verify_password(password):
        return False
    
    g.current_user = user
    g.token_used = False
    return True


@basic_auth.error_handler
def basic_auth_error(status):
    """Basic Auth 错误处理"""
    return unauthorized('Invalid credentials')


def generate_token(user_id):
    """生成API访问令牌"""
    user = User.query.get(user_id)
    if user:
        return user.generate_auth_token()
    return None
