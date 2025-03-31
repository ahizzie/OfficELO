import logging
from flask import Flask, current_app, request
from flask_sqlalchemy import SQLAlchemy
from os import path, makedirs, environ
import os
from flask_login import login_manager
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)

    # Log application startup
    logger.info("Initializing Flask application")

    app.config['SECRET_KEY'] = environ.get('SECRET_KEY', 'fallback')
    logger.debug(f"Using SECRET_KEY: {'*' * len(app.config['SECRET_KEY'])}")

    # Database configuration
    database_uri = environ.get('DATABASE_URL', f'sqlite:///{DB_NAME}')
    logger.info(f"Raw database URI: {database_uri}")

    # Fix PostgreSQL URL format if needed
    if database_uri and database_uri.startswith('postgres://'):
        database_uri = database_uri.replace('postgres://', 'postgresql://', 1)
        logger.info(f"Converted database URI to: {database_uri}")

    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    try:
        db.init_app(app)
        logger.info("SQLAlchemy initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SQLAlchemy: {str(e)}")
        raise

    # Database setup
    if database_uri.startswith('sqlite://'):
        logger.info("SQLite database detected")
        create_database(app)
    else:
        logger.info("Non-SQLite database detected (likely PostgreSQL)")
        try:
            with app.app_context():
                db.create_all()
                logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise

    # Blueprint registration
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    logger.info("Blueprints registered successfully")

    # Login manager setup
    manager = login_manager.LoginManager()
    manager.login_view = 'auth.login'

    try:
        manager.init_app(app)
        logger.info("Login manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize login manager: {str(e)}")
        raise

    @manager.user_loader
    def load_user(id):
        try:
            from .models import User
            user = User.query.get(int(id))
            if not user:
                logger.warning(f"User with ID {id} not found")
            return user
        except Exception as e:
            logger.error(f"Error loading user {id}: {str(e)}")
            return None

    # Add request logging middleware
    @app.before_request
    def log_request_info():
        logger.info(f"Incoming request: {request.method} {request.path}")
        if request.method == 'POST':
            logger.debug(f"Request data: {request.form.to_dict()}")

    @app.after_request
    def log_response_info(response):
        logger.info(f"Outgoing response: {response.status_code}")
        return response

    logger.info("Application initialization complete")
    return app


def create_database(app):
    db_path = path.abspath(path.join(path.dirname(__file__), DB_NAME))
    logger.info(f"Attempting to create database at: {db_path}")

    if not path.exists(db_path):
        try:
            makedirs(path.dirname(db_path), exist_ok=True)
            logger.debug("Database directory created or verified")

            with app.app_context():
                from .models import User, Match
                db.create_all()

                # Log successful creation
                logger.info(f"Database created successfully at {db_path}")

                # Optional: Log tables created
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                logger.debug(f"Tables created: {tables}")

        except Exception as e:
            logger.error(f"Critical error creating database: {str(e)}", exc_info=True)
            raise
    else:
        logger.info(f"Database already exists at {db_path}")