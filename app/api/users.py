from flask import jsonify, request, g, url_for, abort, current_app
from ..models import User, db, Permission, Post
from . import api
from .authentication import basic_auth
from .decorators import permission_required
from .errors import forbidden, unauthorized


@api.route('/users/<int:id>')
def get_user(id):
    """获取用户信息"""
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


@api.route('/users/<username>')
def get_user_by_username(username):
    """通过用户名获取用户信息"""
    user = User.query.filter_by(username=username).first_or_404()
    return jsonify(user.to_json())


@api.route('/users/')
def get_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(
        page=page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out=False)
    users = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_users', page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_users', page=page + 1)

    return jsonify({
        'users': [user.to_json() for user in users],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    """获取用户的文章"""
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', id=id, page=page + 1)

    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/tokens/', methods=['POST'])
@basic_auth.login_required
def get_token():
    """获取API令牌
    
    安全限制：
    1. 必须是已认证用户（不能是匿名用户）
    2. 必须使用密码认证（不能使用已有的token来换取新token）
    """
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    
    return jsonify({
        'token': g.current_user.generate_auth_token(expiration=3600),
        'expiration': 3600
    })


@api.route('/users/<int:id>/followers/')
def get_user_followers(id):
    """获取用户粉丝列表"""
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page=page, per_page=20, error_out=False)
    follows = [{'user': item.follower.to_json(), 'timestamp': item.timestamp}
               for item in pagination.items]

    return jsonify({
        'followers': follows,
        'count': pagination.total
    })


@api.route('/users/<int:id>/followed/')
def get_user_followed(id):
    """获取用户关注列表"""
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page=page, per_page=20, error_out=False)
    follows = [{'user': item.followed.to_json(), 'timestamp': item.timestamp}
               for item in pagination.items]

    return jsonify({
        'followed': follows,
        'count': pagination.total
    })


@api.route('/users/<int:id>/follow/', methods=['POST'])
@basic_auth.login_required
@permission_required(Permission.FOLLOW)
def follow(id):
    """关注用户"""
    user = User.query.get_or_404(id)
    if g.current_user.is_following(user):
        return jsonify({'message': 'Already following'})

    g.current_user.follow(user)
    db.session.commit()
    return jsonify(user.to_json())


@api.route('/users/<int:id>/unfollow/', methods=['POST'])
@basic_auth.login_required
@permission_required(Permission.FOLLOW)
def unfollow(id):
    """取消关注用户"""
    user = User.query.get_or_404(id)
    if not g.current_user.is_following(user):
        return jsonify({'message': 'Not following'})

    g.current_user.unfollow(user)
    db.session.commit()
    return jsonify(user.to_json())
