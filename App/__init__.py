from flask import Flask, current_app, request
from flask_sqlalchemy import SQLAlchemy
from os import path, makedirs, environ
from flask_login import login_manager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
DB_NAME = "database.db"


def is_production(app):
    """
    Checks if the application is likely running on PythonAnywhere.
    """
    return 'PYTHONANYWHERE_SITE' in environ


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = environ.get('SECRET_KEY', 'fallback')

    if is_production(app):
        database_uri = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
            username="ahizzie",
            password="tDm8V5eb6MJCHPB",
            hostname="ahizzie.mysql.pythonanywhere-services.com",
            databasename="ahizzie$final2",
        )
    else:
        database_uri = environ.get('DATABASE_URL', f'sqlite:///{DB_NAME}')

    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri  # Use the processed URI
    app.config["SQLALCHEMY_POOL_RECYCLE"] = {'pool_recycle': 280}
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .models import User, Match

    if database_uri.startswith('sqlite://'):
        create_database(app)
    else:
        with app.app_context():
            db.create_all()

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    manager = login_manager.LoginManager()
    manager.login_view = 'auth.login'
    manager.init_app(app)

    @manager.user_loader
    def load_user(id):
        from .models import User
        return User.query.get(int(id))

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

