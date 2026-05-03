from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_pagedown.fields import PageDownField
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, PasswordField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError, EqualTo
from app.models import Role, User, Category, Tag


class NameForm(FlaskForm):
    name = StringField('你的名字？', validators=[DataRequired()])
    submit = SubmitField('提交')


class PostForm(FlaskForm):
    """发布帖子表单"""
    title = StringField('文章标题', validators=[DataRequired(), Length(1, 128)])
    body = TextAreaField("文章内容", validators=[DataRequired()])
    category = SelectField('分类', coerce=int, validators=[DataRequired()])
    tags = SelectMultipleField('标签', coerce=int)
    submit = SubmitField('发布')
    
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        self.tags.choices = [(t.id, t.name) for t in Tag.query.order_by(Tag.name).all()]


class EditPostForm(FlaskForm):
    """编辑帖子表单"""
    title = StringField('文章标题', validators=[DataRequired(), Length(1, 128)])
    body = TextAreaField("文章内容", validators=[DataRequired()])
    category = SelectField('分类', coerce=int, validators=[DataRequired()])
    tags = SelectMultipleField('标签', coerce=int)
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(EditPostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        self.tags.choices = [(t.id, t.name) for t in Tag.query.order_by(Tag.name).all()]


class EditProfileForm(FlaskForm):
    """编辑个人资料表单"""
    name = StringField('昵称', validators=[Length(0, 64)])
    location = StringField('所在城市', validators=[Length(0, 64)])
    signature = StringField('个人签名', validators=[Length(0, 128)])
    about_me = TextAreaField('个人介绍')
    website = StringField('个人网站', validators=[Length(0, 128)])
    avatar = FileField('上传头像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片文件！')
    ])
    submit = SubmitField('保存')


class ChangePasswordForm(FlaskForm):
    """修改密码表单"""
    old_password = PasswordField('当前密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(),
        EqualTo('password2', message='两次输入的密码必须一致')
    ])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('修改密码')


class ChangeEmailForm(FlaskForm):
    """修改邮箱表单"""
    email = StringField('新邮箱', validators=[
        DataRequired(),
        Length(1, 64),
        Email()
    ])
    password = PasswordField('当前密码', validators=[DataRequired()])
    submit = SubmitField('修改邮箱')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')


class EditProfileAdminForm(FlaskForm):
    """管理员编辑用户资料表单"""
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               '用户名只能包含字母、数字、点或下划线')
    ])
    confirmed = BooleanField('已确认')
    role = SelectField('角色', coerce=int)
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('位置', validators=[Length(0, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('保存')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangeAvatarForm(FlaskForm):
    """更换头像表单"""
    avatar = FileField('选择图片', validators=[
        FileRequired('请选择一个文件'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片文件！')
    ])
    submit = SubmitField('上传')


class CommentForm(FlaskForm):
    """评论表单"""
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('提交评论')


class NavigationForm(FlaskForm):
    """导航菜单表单"""
    name = StringField('名称', validators=[DataRequired(), Length(1, 64)])
    url = StringField('链接地址', validators=[DataRequired(), Length(1, 128)])
    icon = StringField('图标', validators=[Length(0, 64)])
    order = StringField('排序', validators=[Length(0, 10)])
    enabled = BooleanField('启用')
    submit = SubmitField('保存')
