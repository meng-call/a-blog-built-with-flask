from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Email, Regexp
from app.models import User


class LoginForm(FlaskForm):
    """登录表单"""
    email = StringField('邮箱或用户名', validators=[
        DataRequired(),
        Length(1, 64)
    ])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    """注册表单"""
    email = StringField('邮箱', validators=[
        DataRequired(),
        Length(1, 64),
        Email()
    ])
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               '用户名只能包含字母、数字、点或下划线，且必须以字母开头')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(),
        EqualTo('password2', message='两次输入的密码必须一致')
    ])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')

