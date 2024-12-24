from . import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets

class DownloadToken(db.Model):
    __tablename__ = 'download_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    firmware_id = db.Column(db.Integer, db.ForeignKey('firmwares.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def generate_token(firmware_id, user_id, payment_id=None, expires_in=timedelta(hours=24)):
        """Generate a new download token"""
        token = DownloadToken(
            token=secrets.token_urlsafe(32),
            firmware_id=firmware_id,
            user_id=user_id,
            payment_id=payment_id,
            expires_at=datetime.utcnow() + expires_in
        )
        db.session.add(token)
        db.session.commit()
        return token

    def is_valid(self):
        """Check if token is valid"""
        return not self.is_used and datetime.utcnow() <= self.expires_at

    def use_token(self):
        """Mark token as used"""
        if self.is_valid():
            self.is_used = True
            self.used_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

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
    
    def __init__(self, username, email, password, is_admin=False, is_verified=False):
        self.username = username
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.is_verified = is_verified

class BrandCategory(db.Model):
    __tablename__ = 'brand_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    brands = db.relationship('Brand', backref='category', lazy=True)

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    logo_path = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('brand_categories.id'), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    support_phone = db.Column(db.String(20), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')  # active, inactive, pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    firmwares = db.relationship('Firmware', backref='brand', lazy=True)
    
    def __init__(self, name, description=None, logo_path=None, category_id=None,
                 website=None, contact_email=None, support_phone=None):
        self.name = name
        self.description = description
        self.logo_path = logo_path
        self.category_id = category_id
        self.website = website
        self.contact_email = contact_email
        self.support_phone = support_phone

class Firmware(db.Model):
    __tablename__ = 'firmwares'
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    gmail_link = db.Column(db.String(500), nullable=False)
    icon_path = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False)
    downloads = db.Column(db.Integer, default=0, nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    payments = db.relationship('Payment', 
                             backref='firmware', 
                             lazy=True, 
                             cascade='all, delete-orphan')
    download_tokens = db.relationship('DownloadToken',
                                    backref='firmware',
                                    lazy=True,
                                    cascade='all, delete-orphan')

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    firmware_id = db.Column(db.Integer, db.ForeignKey('firmwares.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    withdrawn = db.Column(db.Boolean, default=False, nullable=False)
