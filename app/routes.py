from app.decorators import admin_required, permission_required
from flask import Blueprint, render_template, session, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime, timezone
from .forms import PostForm, EditPostForm, CommentForm, EditProfileForm, ChangeAvatarForm, NavigationForm
from .models import User, db, Post, Comment, Category, Tag, Navigation
from app.models import Role, Permission

main = Blueprint('main', __name__)


@main.after_app_request
def after_request(response):
    """记录慢查询日志"""
    try:
        from flask_sqlalchemy import get_recorded_queries
        queries = get_recorded_queries()
        if queries:
            for query in queries:
                if query.duration >= current_app.config.get('FLASKY_SLOW_DB_QUERY_TIME', 0.5):
                    current_app.logger.warning(
                        'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
                        (query.statement, query.parameters, query.duration, query.context))
    except ImportError:
        # 如果导入失败（旧版本），使用原来的方法
        pass
    return response


@main.app_context_processor
def inject_permissions():
    """注入权限常量到模板"""
    return dict(Permission=Permission)


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    
    page = request.args.get('page', 1, type=int)
    
    query = Post.query
    
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False
    )
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination)


@main.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """发布新文章（仅管理员）"""
    if not current_user.is_administrator():
        abort(403)
    
    form = PostForm()
    if form.validate_on_submit():
        category = Category.query.get(form.category.data)
        post = Post(
            title=form.title.data,
            body=form.body.data,
            category=category,
            author=current_user._get_current_object()
        )
        
        if form.tags.data:
            tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
            post.tags = tags
        
        db.session.add(post)
        db.session.commit()
        flash('文章已发布', 'success')
        return redirect(url_for('.post', id=post.id))
    
    return render_template('edit_post.html', form=form, post=None)


@main.route('/search')
def search():
    """搜索文章"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('.index'))
    
    # 在标题和正文中搜索
    search_pattern = f'%{query}%'
    posts = Post.query.filter(
        db.or_(
            Post.title.like(search_pattern),
            Post.body.like(search_pattern)
        )
    ).order_by(Post.timestamp.desc()).paginate(
        page=page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    
    return render_template('search.html', posts=posts, query=query, pagination=posts)


@main.route('/about')
def about():
    """关于我页面"""
    return render_template('about.html')


@main.route('/user/<username>')
def user(username):
    """用户资料页面"""
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.signature = form.signature.data
        current_user.about_me = form.about_me.data
        current_user.website = form.website.data
        
        # 处理头像上传
        if form.avatar.data:
            current_user.save_avatar(form.avatar.data)
        
        db.session.add(current_user)
        db.session.commit()
        flash('你的个人资料已更新', 'success')
        return redirect(url_for('main.user', username=current_user.username))
    
    if request.method == 'GET':
        form.name.data = current_user.name
        form.location.data = current_user.location
        form.signature.data = current_user.signature
        form.about_me.data = current_user.about_me
        if hasattr(current_user, 'website'):
            form.website.data = current_user.website
    
    return render_template('edit_profile.html', form=form)


@main.route('/change-avatar', methods=['GET', 'POST'])
@login_required
def change_avatar():
    """更换头像"""
    form = ChangeAvatarForm()
    if form.validate_on_submit():
        try:
            current_user.save_avatar(form.avatar.data)
            db.session.add(current_user)
            db.session.commit()
            flash('头像已成功更新', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'头像上传失败: {str(e)}', 'danger')
            return redirect(url_for('main.change_avatar'))
        return redirect(url_for('main.user', username=current_user.username))
    
    return render_template('auth/change_avatar.html', form=form)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    """文章详情页"""
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post,
                         author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('你的评论已发布', 'success')
        return redirect(url_for('.post', id=post.id, page=-1))
    
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
               current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    
    pagination = post.comments.filter_by(disabled=False).order_by(Comment.timestamp.asc()).paginate(
        page=page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    
    return render_template('post.html', posts=[post], form=form,
                          comments=comments, pagination=pagination)


@main.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    """编辑文章"""
    post = Post.query.get_or_404(id)
    if current_user != post.author:
        abort(403)
    
    form = EditPostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        
        category = Category.query.get(form.category.data)
        post.category = category
        
        if form.tags.data:
            tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
            post.tags = tags
        
        db.session.add(post)
        db.session.commit()
        flash('文章已更新', 'success')
        return redirect(url_for('.post', id=post.id))
    
    if request.method == 'GET':
        form.title.data = post.title
        form.body.data = post.body
        form.category.data = post.category_id if post.category else None
        form.tags.data = [tag.id for tag in post.tags]
    
    return render_template('edit_post.html', form=form, post=post)


@main.route('/post/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    """删除文章"""
    post = Post.query.get_or_404(id)
    if current_user != post.author:
        abort(403)
    
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除', 'success')
    return redirect(url_for('.index'))


@main.route('/archives')
def archives():
    """归档页面 - 按年份和月份分组显示文章"""
    from sqlalchemy import extract
    
    # 获取所有年份和月份
    archives = db.session.query(
        extract('year', Post.timestamp).label('year'),
        extract('month', Post.timestamp).label('month')
    ).group_by('year', 'month').order_by(
        db.desc('year'), db.desc('month')
    ).all()
    
    archive_data = []
    for year, month in archives:
        posts = Post.query.filter(
            extract('year', Post.timestamp) == year,
            extract('month', Post.timestamp) == month
        ).order_by(Post.timestamp.desc()).all()
        archive_data.append({
            'year': int(year),
            'month': int(month),
            'posts': posts
        })
    
    return render_template('archives.html', archives=archive_data)


@main.route('/categories')
def categories():
    """分类页面"""
    category_list = Category.query.all()
    return render_template('categories.html', categories=category_list)


@main.route('/category/<int:id>')
def category(id):
    """分类详情页"""
    category = Category.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(category_id=id).order_by(
        Post.timestamp.desc()
    ).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    return render_template('category.html', category=category,
                          posts=pagination.items, pagination=pagination)


@main.route('/tags')
def tags():
    """标签页面"""
    tag_list = Tag.query.all()
    return render_template('tags.html', tags=tag_list)


@main.route('/tag/<int:id>')
def tag(id):
    """标签详情页"""
    tag_obj = Tag.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = tag_obj.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    return render_template('tag.html', tag=tag_obj,
                          posts=pagination.items, pagination=pagination)


@main.route('/admin/categories')
@login_required
def admin_categories():
    """分类管理页面"""
    if not current_user.is_administrator():
        abort(403)
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)


@main.route('/admin/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """添加分类"""
    if not current_user.is_administrator():
        abort(403)
    from flask import request as req
    if req.method == 'POST':
        name = req.form.get('name', '').strip()
        if name:
            if Category.query.filter_by(name=name).first():
                flash('分类已存在', 'warning')
            else:
                category = Category(name=name)
                db.session.add(category)
                db.session.commit()
                flash('分类已添加', 'success')
                return redirect(url_for('.admin_categories'))
    return render_template('admin/category_form.html', title='添加分类')


@main.route('/admin/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """编辑分类"""
    if not current_user.is_administrator():
        abort(403)
    category = Category.query.get_or_404(id)
    from flask import request as req
    if req.method == 'POST':
        name = req.form.get('name', '').strip()
        if name:
            existing = Category.query.filter_by(name=name).first()
            if existing and existing.id != id:
                flash('分类名称已存在', 'warning')
            else:
                category.name = name
                db.session.add(category)
                db.session.commit()
                flash('分类已更新', 'success')
                return redirect(url_for('.admin_categories'))
    return render_template('admin/category_form.html', category=category, title='编辑分类')


@main.route('/admin/category/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    """删除分类"""
    if not current_user.is_administrator():
        abort(403)
    category = Category.query.get_or_404(id)
    if category.posts.count() > 0:
        flash('该分类下有文章，无法删除', 'warning')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类已删除', 'success')
    return redirect(url_for('.admin_categories'))


@main.route('/admin/tags')
@login_required
def admin_tags():
    """标签管理页面"""
    if not current_user.is_administrator():
        abort(403)
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('admin/tags.html', tags=tags)


@main.route('/admin/tag/add', methods=['GET', 'POST'])
@login_required
def add_tag():
    """添加标签"""
    if not current_user.is_administrator():
        abort(403)
    from flask import request as req
    if req.method == 'POST':
        name = req.form.get('name', '').strip()
        if name:
            if Tag.query.filter_by(name=name).first():
                flash('标签已存在', 'warning')
            else:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
                flash('标签已添加', 'success')
                return redirect(url_for('.admin_tags'))
    return render_template('admin/tag_form.html', title='添加标签')


@main.route('/admin/tag/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tag(id):
    """编辑标签"""
    if not current_user.is_administrator():
        abort(403)
    tag = Tag.query.get_or_404(id)
    from flask import request as req
    if req.method == 'POST':
        name = req.form.get('name', '').strip()
        if name:
            existing = Tag.query.filter_by(name=name).first()
            if existing and existing.id != id:
                flash('标签名称已存在', 'warning')
            else:
                tag.name = name
                db.session.add(tag)
                db.session.commit()
                flash('标签已更新', 'success')
                return redirect(url_for('.admin_tags'))
    return render_template('admin/tag_form.html', tag=tag, title='编辑标签')


@main.route('/admin/tag/<int:id>/delete', methods=['POST'])
@login_required
def delete_tag(id):
    """删除标签"""
    if not current_user.is_administrator():
        abort(403)
    tag = Tag.query.get_or_404(id)
    if tag.posts.count() > 0:
        flash('该标签下有文章，无法删除', 'warning')
    else:
        db.session.delete(tag)
        db.session.commit()
        flash('标签已删除', 'success')
    return redirect(url_for('.admin_tags'))


@main.app_context_processor
def inject_navigations():
    """注入导航菜单到所有模板"""
    navs = Navigation.query.filter_by(enabled=True).order_by(Navigation.order).all()
    return dict(custom_navigations=navs)

@main.route('/admin/navigations')
@login_required
def admin_navigations():
    """导航菜单管理页面"""
    if not current_user.is_administrator():
        abort(403)
    navs = Navigation.query.order_by(Navigation.order).all()
    return render_template('admin/navigations.html', navs=navs)


@main.route('/admin/navigation/add', methods=['GET', 'POST'])
@login_required
def add_navigation():
    """添加导航菜单"""
    if not current_user.is_administrator():
        abort(403)
    form = NavigationForm()
    if form.validate_on_submit():
        nav = Navigation(
            name=form.name.data,
            url=form.url.data,
            icon=form.icon.data or 'fas fa-link',
            order=int(form.order.data) if form.order.data else 0,
            enabled=form.enabled.data
        )
        db.session.add(nav)
        db.session.commit()
        flash('导航菜单已添加', 'success')
        return redirect(url_for('.admin_navigations'))
    return render_template('admin/navigation_form.html', form=form, title='添加导航')


@main.route('/admin/navigation/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_navigation(id):
    """编辑导航菜单"""
    if not current_user.is_administrator():
        abort(403)
    nav = Navigation.query.get_or_404(id)
    form = NavigationForm()
    if form.validate_on_submit():
        nav.name = form.name.data
        nav.url = form.url.data
        nav.icon = form.icon.data or 'fas fa-link'
        nav.order = int(form.order.data) if form.order.data else 0
        nav.enabled = form.enabled.data
        db.session.add(nav)
        db.session.commit()
        flash('导航菜单已更新', 'success')
        return redirect(url_for('.admin_navigations'))
    
    if request.method == 'GET':
        form.name.data = nav.name
        form.url.data = nav.url
        form.icon.data = nav.icon
        form.order.data = str(nav.order)
        form.enabled.data = nav.enabled
    
    return render_template('admin/navigation_form.html', form=form, title='编辑导航')


@main.route('/admin/navigation/<int:id>/delete', methods=['POST'])
@login_required
def delete_navigation(id):
    """删除导航菜单"""
    if not current_user.is_administrator():
        abort(403)
    nav = Navigation.query.get_or_404(id)
    db.session.delete(nav)
    db.session.commit()
    flash('导航菜单已删除', 'success')
    return redirect(url_for('.admin_navigations'))


@main.route('/upload-editor-image', methods=['POST'])
@login_required
def upload_editor_image():
    """上传编辑器图片"""
    from flask import request as req
    from werkzeug.utils import secure_filename
    import os
    from uuid import uuid4
    
    if 'file' not in req.files:
        return {'error': 'No file provided'}, 400
    
    file = req.files['file']
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    # 验证文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in allowed_extensions:
        return {'error': 'File type not allowed'}, 400
    
    # 生成唯一文件名
    new_filename = f'{uuid4().hex}.{ext}'
    
    # 保存文件
    static_folder = current_app.static_folder
    upload_dir = os.path.join(static_folder, 'uploads', 'editor')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, new_filename)
    file.save(file_path)
    
    # 返回图片URL
    image_url = url_for('static', filename=f'uploads/editor/{new_filename}')
    
    return {'location': image_url}, 200


@main.app_context_processor
def inject_navigations():
    """注入导航菜单到所有模板"""
    navs = Navigation.query.filter_by(enabled=True).order_by(Navigation.order).all()
    return dict(custom_navigations=navs)
