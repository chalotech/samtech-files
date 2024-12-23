from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon_path = db.Column(db.String(255))
    description = db.Column(db.Text)
    firmwares = db.relationship('Firmware', backref='brand', lazy=True)

class Firmware(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100))
    version = db.Column(db.String(50))
    description = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    icon_path = db.Column(db.String(200))
    price = db.Column(db.Float, default=0.0)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    downloads = db.Column(db.Integer, default=0)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    firmware_id = db.Column(db.Integer, db.ForeignKey('firmware.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    withdrawn = db.Column(db.Boolean, default=False)
    
    firmware = db.relationship('Firmware', backref='payments')
    user = db.relationship('User', backref='payments')

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    admin = db.relationship('User', backref='withdrawals')
    
    def __repr__(self):
        return f'<Withdrawal {self.amount} to {self.phone_number}>'
