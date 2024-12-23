from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from .config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
mail = Mail()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure logging
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_handler = RotatingFileHandler(os.path.join(log_dir, 'samtech.log'), maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Samtech startup')

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Error loading user: {str(e)}")
            return None
    
    # Initialize database
    with app.app_context():
        try:
            app.logger.info("Checking database status...")
            db.create_all()
            app.logger.info("Database tables created/verified successfully")
            
            # Initialize default data
            from .init_db import init_db
            init_db(app)
            
            # Check if admin user exists
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                app.logger.info("No admin user found. Creating default admin...")
                from .init_db import create_admin_user
                create_admin_user()
                
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            raise  # We want to know if database init fails
    
    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .mpesa import mpesa as mpesa_blueprint
    app.register_blueprint(mpesa_blueprint, url_prefix='/mpesa')
    
    from .firmware import firmware as firmware_blueprint
    app.register_blueprint(firmware_blueprint, url_prefix='/firmware')
    
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    return app
