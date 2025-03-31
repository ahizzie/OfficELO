import logging
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from os import path, makedirs, environ
import os
from flask_login import login_manager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)

    # Determine environment and set configuration
    if 'DATABASE_URL' in os.environ:
        # Production (Heroku)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace("postgres://", "postgresql://", 1)  # Heroku's postgres url starts with postgres://, need to replace with postgresql:// for sqlalchemy
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress deprecation warning
        logging.log("USED POSTGRES!")
    else:
        # Development/Testing
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "dev_secret_key")  # Use environment variable for production, or a default for development.

    db.init_app(app)

    # Import and register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Login manager setup
    from flask_login import LoginManager
    manager = login_manager.LoginManager()
    manager.login_view = 'auth.login'
    manager.init_app(app)

    # Create tables within app context
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            logging.error(f"Error creating tables: {e}")

    @manager.user_loader
    def load_user(id):
        from .models import User
        return User.query.get(int(id))

    return app


