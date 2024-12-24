from . import db
from .models import User, Brand
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

def create_admin_user():
    """Create admin user if not exists"""
    try:
        logger.info("Creating admin user...")
        
        # Check if admin exists
        admin = User.query.filter_by(username='samtech').first()
        if not admin:
            admin = User(
                username='samtech',
                email='samtech@gmail.com',
                password=generate_password_hash('samuel', method='sha256'),
                is_admin=True,
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.session.rollback()
        raise

def create_default_brands():
    """Create default brands if not exist"""
    try:
        logger.info("Creating default brands...")
        default_brands = [
            {'name': 'Samsung', 'description': 'Samsung Electronics'},
            {'name': 'LG', 'description': 'LG Electronics'},
            {'name': 'Sony', 'description': 'Sony Electronics'},
            {'name': 'Hisense', 'description': 'Hisense Electronics'},
            {'name': 'TCL', 'description': 'TCL Electronics'}
        ]
        
        brands_created = 0
        for brand_data in default_brands:
            if not Brand.query.filter_by(name=brand_data['name']).first():
                brand = Brand(**brand_data)
                db.session.add(brand)
                brands_created += 1
        
        if brands_created > 0:
            db.session.commit()
            logger.info(f"Created {brands_created} default brands")
        else:
            logger.info("Default brands already exist")
    except Exception as e:
        logger.error(f"Error creating default brands: {str(e)}")
        db.session.rollback()
        raise

def init_db(app):
    """Initialize database with default data"""
    try:
        # Ensure uploads directory exists
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            logger.info(f"Created uploads directory at {uploads_dir}")
        
        # Create admin user
        create_admin_user()
        
        # Create default brands
        create_default_brands()
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
