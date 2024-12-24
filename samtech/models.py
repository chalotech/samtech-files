from . import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets

class DownloadToken(db.Model):
    __tablename__ = 'download_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, nullable=False)
    download_count = db.Column(db.Integer, default=0)
    firmware_id = db.Column(db.Integer, db.ForeignKey('firmwares.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, token, firmware_id, user_id, expires_at):
        self.token = token
        self.firmware_id = firmware_id
        self.user_id = user_id
        self.expires_at = expires_at

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(32), unique=True, nullable=True)
    verification_code_expiry = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(32), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='user', lazy=True)
    downloads = db.relationship('DownloadToken', backref='user', lazy=True)
    firmwares = db.relationship('Firmware', backref='creator', lazy=True)
    
    def __init__(self, username, email, password, is_admin=False, is_verified=False, verification_code=None, verification_code_expiry=None):
        self.username = username
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.is_verified = is_verified
        self.verification_code = verification_code
        self.verification_code_expiry = verification_code_expiry

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    logo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    firmwares = db.relationship('Firmware', back_populates='brand', lazy=True)

class Firmware(db.Model):
    __tablename__ = 'firmwares'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    features = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255))
    size = db.Column(db.Integer)
    price = db.Column(db.Float, default=0.0)
    downloads = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    brand = db.relationship('Brand', backref=db.backref('firmwares', lazy=True))
    creator = db.relationship('User', backref=db.backref('firmwares', lazy=True))
    
    def __repr__(self):
        return f'<Firmware {self.name} v{self.version}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    phone_number = db.Column(db.String(15), nullable=False)
    checkout_request_id = db.Column(db.String(50), unique=True, nullable=True)
    mpesa_receipt = db.Column(db.String(20), unique=True, nullable=True)
    mpesa_date = db.Column(db.String(14), nullable=True)
    failure_reason = db.Column(db.String(200), nullable=True)
    firmware_id = db.Column(db.Integer, db.ForeignKey('firmwares.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, reference, amount, phone_number, firmware_id, user_id):
        self.reference = reference
        self.amount = amount
        self.phone_number = phone_number
        self.firmware_id = firmware_id
        self.user_id = user_id
