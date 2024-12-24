from . import db
from .models import User, Brand
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_admin_user():
    """Create admin user if not exists"""
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

def create_default_brands():
    """Create default brands if not exist"""
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

def init_db(app):
    """Initialize database with default data"""
    with app.app_context():
        try:
            create_admin_user()
            create_default_brands()
            logger.info("Database initialization completed successfully")
        except Exception as e:
            logger.error(f"Error during database initialization: {str(e)}")
            raise
