from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
# from flask_socketio import SocketIO, emit

# Globally accessible libraries
login_manager = LoginManager()
csrf = CSRFProtect()
# socketio = SocketIO()

def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.DevConfig')
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
    app.config[ 'UPLOAD_FOLDER' ] = UPLOAD_FOLDER
    app.config[ 'MAX_CONTENT_LENGTH' ] = 70 * 1024 * 1024

    # Initialize Plugins
    login_manager.init_app(app)
    csrf.init_app(app)
    # socketio.init_app(app)


    with app.app_context():
        # Include our Routes
        from .CLIENT.routes import agent_bp


        # Register Blueprints
        app.register_blueprint(agent_bp)

        return app