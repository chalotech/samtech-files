from . import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import relationship
import secrets

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_code = db.Column(db.String(6))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    firmwares = relationship('Firmware', backref='creator', lazy=True)
    payments = relationship('Payment', backref='user', lazy=True)
    withdrawals = relationship('Withdrawal', backref='user', lazy=True)

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon_path = db.Column(db.String(255))
    description = db.Column(TEXT)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships with cascade
    firmwares = relationship('Firmware', 
                           backref='brand', 
                           lazy=True, 
                           cascade='all, delete-orphan')

class Firmware(db.Model):
    __tablename__ = 'firmwares'
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    description = db.Column(TEXT)
    gmail_link = db.Column(db.String(500), nullable=False)  # Store Gmail sharing link
    icon_path = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False)
    downloads = db.Column(db.Integer, default=0, nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships with cascade
    payments = relationship('Payment', 
                          backref='firmware', 
                          lazy=True, 
                          cascade='all, delete-orphan')
    download_links = relationship('DownloadLink',
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

class DownloadLink(db.Model):
    __tablename__ = 'download_links'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    firmware_id = db.Column(db.Integer, db.ForeignKey('firmwares.id', ondelete='CASCADE'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime)
    
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_for_payment(payment, expiry_hours=24):
        token = DownloadLink.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        link = DownloadLink(
            token=token,
            firmware_id=payment.firmware_id,
            payment_id=payment.id,
            expires_at=expires_at
        )
        db.session.add(link)
        db.session.commit()
        return link
    
    def is_valid(self):
        return (
            not self.used and
            datetime.utcnow() <= self.expires_at
        )
    
    def mark_as_used(self):
        self.used = True
        self.used_at = datetime.utcnow()
        db.session.commit()

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
