import logging
from samtech import db, create_app
from samtech.models import User, Brand, Firmware, Payment, DownloadToken

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_database():
    """Recreate the database by dropping all tables and creating them again"""
    try:
        logger.info("Starting database recreation...")
        
        # Create app context
        app = create_app()
        with app.app_context():
            # Drop all tables
            logger.info("Dropping all tables...")
            db.drop_all()
            logger.info("All tables dropped successfully")
            
            # Create all tables
            logger.info("Creating all tables...")
            db.create_all()
            logger.info("All tables created successfully")
            
            logger.info("Database recreation completed successfully!")
            
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        raise

if __name__ == "__main__":
    recreate_database()
