from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, RegistrationForm
from app.models import User, Permission
from app import db
from app.email import send_email
from app.decorators import permission_required, admin_required


@auth.before_app_request
def before_request():
    """在每次请求前检查用户是否已确认"""
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    """未确认账户提示页面"""
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    form = LoginForm()
    
    if form.validate_on_submit():
        print(f"Login attempt: {form.email.data}")
        
        # 尝试用邮箱或用户名查找用户
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            user = User.query.filter_by(username=form.email.data).first()

        if user is None or not user.verify_password(form.password.data):
            print(f"Login failed for: {form.email.data}")
            flash('邮箱/用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        print(f"Login successful: {user.username}")
        flash('登录成功', 'success')
        return redirect(next_page or url_for('main.index'))
    
    if form.is_submitted():
        print(f"Form validation failed")
        print(f"Errors: {form.errors}")

    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            new_user = User(username=form.username.data, email=form.email.data)
            new_user.password = form.password.data
            
            from app.models import Role
            default_role = Role.query.filter_by(default=True).first()
            if default_role:
                new_user.role = default_role
            
            db.session.add(new_user)
            db.session.commit()
            
            # 在开发环境下自动确认账户，不发送邮件
            from flask import current_app
            if current_app.config.get('DEBUG'):
                new_user.confirmed = True
                db.session.commit()
                flash('注册成功！您的账户已自动确认（开发模式）', 'success')
            else:
                token = new_user.generate_confirmation_token()
                send_email(
                    new_user.email,
                    'Confirm Your Account',
                    'auth/email/confirm',
                    user=new_user,
                    token=token
                )
                flash('确认邮件已发送到您的邮箱', 'info')
            
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败，请稍后重试: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    """确认用户账户"""
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    
    if current_user.confirm(token):
        db.session.commit()
        flash('您的账户已确认，谢谢！', 'success')
    else:
        flash('确认链接无效或已过期', 'danger')
    
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    """重新发送确认邮件"""
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    
    token = current_user.generate_confirmation_token()
    send_email(
        current_user.email,
        'Confirm Your Account',
        'auth/email/confirm',
        user=current_user,
        token=token
    )
    flash('新的确认邮件已发送到您的邮箱', 'info')
    return redirect(url_for('main.index'))


@auth.route('/write-post')
@login_required
@permission_required(Permission.WRITE)
def write_post():
    """只有有 WRITE 权限的用户才能访问"""
    return 'Write a new post'


@auth.route('/moderate-comments')
@login_required
@permission_required(Permission.MODERATE)
def moderate_comments():
    """只有有 MODERATE 权限的用户才能访问"""
    return 'Moderate comments'


@auth.route('/admin-panel')
@login_required
@admin_required
def admin_panel():
    """只有管理员才能访问"""
    return 'Admin panel'


@auth.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('main.index'))


@auth.route('/secret')
@login_required
def secret():
    """受保护的页面，只有认证用户可以访问"""
    return 'Only authenticated users are allowed!'
