import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

def create_app():
    """Create and configure an instance of the Flask application."""
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    # --- Configuration ---
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise ValueError("A SECRET_KEY must be set in the environment variables or .env file.")
    app.config['SECRET_KEY'] = secret_key

    # --- Database Session Management ---
    from .database import db_session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # --- Register Blueprints ---
    from .blueprints import auth, user, data, processing, server_admin
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(user.user_bp)
    app.register_blueprint(data.data_bp)
    app.register_blueprint(processing.processing_bp)
    app.register_blueprint(server_admin.admin_bp)

    # --- Initialize Global Services ---
    with app.app_context():
        from .server import initialize_app_components
        initialize_app_components()

    return app
