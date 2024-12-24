from werkzeug.security import generate_password_hash
from datetime import datetime
from . import db
from .models import User, Brand

def init_db(app):
    """Initialize the database with default data"""
    with app.app_context():
        app.logger.info("Checking for initial data...")
        
        # Check if we need to create an admin user
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            app.logger.info("Creating admin user...")
            admin = User(
                email="admin@samtech.com",
                username="admin",
                password=generate_password_hash("admin123", method='sha256'),
                is_admin=True,
                email_verified=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Admin user created successfully")
        
        # Check if we need to create default brands
        if Brand.query.count() == 0:
            app.logger.info("Creating default brands...")
            default_brands = [
                {
                    "name": "Samsung",
                    "description": "Samsung mobile phones and tablets"
                },
                {
                    "name": "iPhone",
                    "description": "Apple iPhones and iOS devices"
                },
                {
                    "name": "Tecno",
                    "description": "Tecno mobile devices"
                },
                {
                    "name": "Infinix",
                    "description": "Infinix smartphones"
                },
                {
                    "name": "Oppo",
                    "description": "Oppo smartphones and accessories"
                }
            ]
            
            for brand_data in default_brands:
                brand = Brand(
                    name=brand_data["name"],
                    description=brand_data["description"],
                    created_at=datetime.utcnow()
                )
                db.session.add(brand)
            
            db.session.commit()
            app.logger.info(f"Created {len(default_brands)} default brands")
        
        app.logger.info("Database initialization completed")
