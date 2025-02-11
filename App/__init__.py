from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path, makedirs
from flask_login import login_manager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'a'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{path.abspath(path.join(path.dirname(__file__), DB_NAME))}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Match

    with app.app_context():
        db.create_all()

    manager = login_manager.LoginManager()
    manager.login_view = 'auth.login'
    manager.init_app(app)

    create_database(app)

    @manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    db_path = path.abspath(path.join(path.dirname(__file__), DB_NAME))
    if not path.exists(db_path):
        try:
            makedirs(path.dirname(db_path), exist_ok=True)
            with app.app_context():
                db.create_all()
        except Exception as e:
            print(f"Error creating database: {e}")

