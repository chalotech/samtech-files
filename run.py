import os
import logging
from logging.handlers import RotatingFileHandler
from samtech import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Create the Flask application
    app = create_app()

    # Configure production logging
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up file logging
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'samtech.log'),
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        db.session.rollback()
        return "Internal Server Error", 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        app.logger.error(f'Unhandled Exception: {e}')
        db.session.rollback()
        return "Internal Server Error", 500

except Exception as e:
    logger.error(f"Failed to create app: {e}")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
