import logging
from samtech import db, create_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_database():
    try:
        app = create_app()
        with app.app_context():
            logger.info("Starting database recreation...")
            
            # Drop all tables
            logger.info("Dropping all tables...")
            db.drop_all()
            logger.info("All tables dropped successfully")
            
            # Create all tables
            logger.info("Creating all tables...")
            db.create_all()
            logger.info("All tables created successfully")
            
            logger.info("Database recreation completed successfully!")
            return True
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        return False

if __name__ == "__main__":
    success = recreate_database()
    if not success:
        exit(1)
