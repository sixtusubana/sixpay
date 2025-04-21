from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from API.settings import *
from datetime import timedelta

import os

# Globally accessible libraries
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cors = CORS()
jwt = JWTManager()

def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.DevConfig')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=365)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=90)
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
    app.config[ 'UPLOAD_FOLDER' ] = UPLOAD_FOLDER
    app.config[ 'MAX_CONTENT_LENGTH' ] = 200 * 1024 * 1024
    app.config[ 'TESTING' ] = False
    
    #Gmail configuration
    # app.config[ 'MAIL_USE_SSL' ] = True
    # app.config[ 'MAIL_SERVER' ] = 'smtp.gmail.com'
    # app.config[ 'MAIL_PORT' ] = 465
    # app.config[ 'MAIL_USERNAME' ] = App_email
    # app.config[ 'MAIL_PASSWORD' ] = App_password
    # app.config[ 'MAIL_USE_TLS' ] = False
    # app.config[ 'MAIL_USE_SSL' ] = True
    
    #Skolaz Webmail configuaration
    app.config['MAIL_SERVER'] = 'skolaz.com'  # Use the SMTP server from cPanel
    app.config['MAIL_PORT'] = 465  # Use 587 if you prefer STARTTLS
    app.config['MAIL_USE_SSL'] = True  # Use False if you prefer STARTTLS
    app.config['MAIL_USE_TLS'] = False  # Use True if using STARTTLS
    app.config['MAIL_USERNAME'] = App_email
    app.config['MAIL_PASSWORD'] = App_password
    
    app.config[ 'MAIL_DEFAULT_SENDER'] = f"{App_name} <{App_email}>"

    # Initialize Plugins
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        # Include our Routes
        from .AGENT.routes import agent_bp


        # Register Blueprints
        app.register_blueprint(agent_bp, url_prefix="/agent")

        db.create_all()

        return app