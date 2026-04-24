from flask import jsonify, request, g, url_for, abort, current_app
from ..models import Post, User, db, Permission
from . import api
from .authentication import basic_auth
from .decorators import permission_required
from .errors import forbidden


@api.route('/posts/')
def get_posts():
    """获取所有文章列表"""
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config.get('FLASKY_POSTS_PER_PAGE', 20), error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page + 1)

    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/posts/<int:id>')
def get_post(id):
    """获取单篇文章"""
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


@api.route('/posts/', methods=['POST'])
@basic_auth.login_required
@permission_required(Permission.WRITE)
def new_post():
    """创建新文章"""
    post = Post.from_json(request.json)
    post.author = g.current_user

    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_json()), 201, \
        {'Location': url_for('api.get_post', id=post.id)}


@api.route('/posts/<int:id>', methods=['PUT'])
@basic_auth.login_required
def edit_post(id):
    """编辑文章"""
    post = Post.query.get_or_404(id)

    if g.current_user != post.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')

    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_json())


@api.route('/posts/<int:id>', methods=['DELETE'])
@basic_auth.login_required
@permission_required(Permission.ADMIN)
def delete_post(id):
    """删除文章"""
    post = Post.query.get_or_404(id)

    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': 'Post deleted'})
