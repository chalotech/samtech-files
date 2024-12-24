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
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), unique=True, nullable=True)
    verification_code_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    firmwares = db.relationship('Firmware', backref='creator', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    downloads = db.relationship('DownloadToken', backref='user', lazy=True)

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon_path = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    firmwares = db.relationship('Firmware', 
                              backref='brand', 
                              lazy=True, 
                              cascade='all, delete-orphan')

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
