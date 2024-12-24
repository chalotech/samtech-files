import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Print environment variables for debugging (excluding sensitive ones)
    def __init__(self):
        print("Loading configuration...", file=sys.stderr)
        print(f"DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}", file=sys.stderr)
        print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}", file=sys.stderr)
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///samtech.db')
    
    # Set the database URL
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Flask configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PROPAGATE_EXCEPTIONS = True
