from flask import jsonify, request, g, url_for, abort
from ..models import Comment, Post, db, Permission
from . import api
from .authentication import basic_auth
from .decorators import permission_required
from .errors import forbidden


@api.route('/comments/')
@basic_auth.login_required
def get_comments():
    """获取所有评论列表"""
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page + 1)

    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/comments/<int:id>')
def get_comment(id):
    """获取单条评论"""
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api.route('/posts/<int:id>/comments/')
def get_post_comments(id):
    """获取文章的评论"""
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.filter_by(disabled=False).order_by(
        Comment.timestamp.asc()).paginate(
        page=page, per_page=20, error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_post_comments', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_post_comments', id=id, page=page + 1)

    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/posts/<int:id>/comments/', methods=['POST'])
@basic_auth.login_required
@permission_required(Permission.COMMENT)
def new_comment(id):
    """在文章下发布评论"""
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.post = post
    comment.author = g.current_user

    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_json()), 201, \
        {'Location': url_for('api.get_comment', id=comment.id)}


@api.route('/comments/<int:id>', methods=['PUT'])
@basic_auth.login_required
def edit_comment(id):
    """编辑评论"""
    comment = Comment.query.get_or_404(id)

    if g.current_user != comment.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')

    comment.body = request.json.get('body', comment.body)
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_json())


@api.route('/comments/<int:id>', methods=['DELETE'])
@basic_auth.login_required
@permission_required(Permission.ADMIN)
def delete_comment(id):
    """删除评论"""
    comment = Comment.query.get_or_404(id)

    if g.current_user != comment.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'Comment deleted'})


@api.route('/moderate/disable/<int:id>', methods=['POST'])
@basic_auth.login_required
@permission_required(Permission.MODERATE)
def disable_comment(id):
    """禁用评论（需要MODERATE权限）"""
    comment = Comment.query.get_or_404(id)

    comment.disabled = True
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_json())


@api.route('/moderate/enable/<int:id>', methods=['POST'])
@basic_auth.login_required
@permission_required(Permission.MODERATE)
def enable_comment(id):
    """启用评论（需要MODERATE权限）"""
    comment = Comment.query.get_or_404(id)

    comment.disabled = False
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_json())
