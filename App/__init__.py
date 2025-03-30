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
    app.config['SECRET_KEY'] = environ.get('SECRET_KEY', 'fallback')

    # Always use PostgreSQL on Heroku, SQLite only locally
    database_uri = environ.get('DATABASE_URL')
    if not database_uri:
        database_uri = f'sqlite:///{DB_NAME}'
    elif database_uri.startswith('postgres://'):
        database_uri = database_uri.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Import and register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Login manager setup
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        from .models import User
        return User.query.get(int(id))

    # Create tables within app context
    with app.app_context():
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite://'):
            try:
                db.create_all()
                print("Created SQLite database tables")
            except Exception as e:
                print(f"Error creating tables: {e}")

    return app


def create_database(app):
    db_path = path.abspath(path.join(path.dirname(__file__), DB_NAME))
    # db_path = "C:/Users/andrew.hislop/PycharmProjects/OfficELO/App/test_database.db"
    print(f"Database path: {db_path}")
    if not path.exists(db_path):
        try:
            makedirs(path.dirname(db_path), exist_ok=True)
            with app.app_context():
                from .models import User, Match
                db.create_all()
                print("Database created successfully!")
        except Exception as e:
            current_app.logger.error(f"Error creating database: {e}")

