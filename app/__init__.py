import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_pagedown import PageDown
from config import config

db = SQLAlchemy()
migrate = Migrate()
moment = Moment()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()
bootstrap = Bootstrap()
pagedown = PageDown()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG') or 'default'

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])

    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    pagedown.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    from .errors import errors as errors_bp
    app.register_blueprint(errors_bp)

    from .auth import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .api import api as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    return app
