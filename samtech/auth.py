from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .models import User
from flask_mail import Message
import random
import string
from datetime import datetime, timedelta
from . import mail

auth = Blueprint('auth', __name__)

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    msg = Message('Verify your Samtech Firmware Account',
                  sender=('Samtech Firmware', 'chalomtech4@gmail.com'),
                  recipients=[email])
    
    msg.html = render_template('email/verify_email.html',
                             user={'username': email.split('@')[0]},
                             code=code,
                             now=datetime.utcnow())
    
    try:
        mail.send(msg)
        current_app.logger.info(f"Verification email sent to {email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        raise

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))
        
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Send verification email
            verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            new_user.verification_code = verification_code
            new_user.verification_code_expiry = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            
            send_verification_email(new_user.email, verification_code)
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        code = request.form.get('code')
        
        if not code:
            flash('Please enter the verification code', 'error')
            return redirect(url_for('auth.verify_email'))
        
        user = User.query.filter_by(verification_code=code).first()
        
        if not user:
            flash('Invalid verification code', 'error')
            return redirect(url_for('auth.verify_email'))
        
        if user.verification_code_expiry < datetime.utcnow():
            flash('Verification code has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.verify_email'))
        
        user.is_verified = True
        user.verification_code = None
        user.verification_code_expiry = None
        
        try:
            db.session.commit()
            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during email verification: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('verify_email.html')

@auth.route('/resend-verification')
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.query.filter_by(is_verified=False).order_by(User.id.desc()).first()
    
    if not user:
        flash('No pending verification found', 'error')
        return redirect(url_for('auth.login'))
    
    verification_code = generate_verification_code()
    verification_code_expiry = datetime.utcnow() + timedelta(hours=24)
    
    user.verification_code = verification_code
    user.verification_code_expiry = verification_code_expiry
    
    try:
        db.session.commit()
        send_verification_email(user.email, verification_code)
        flash('Verification code resent! Please check your email.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resending verification: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('auth.verify_email'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
