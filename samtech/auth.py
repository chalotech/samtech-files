from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User
from datetime import datetime, timedelta
import random
import string
from .email import send_verification_email

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('auth.login'))

        if not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('auth.login'))

        if not user.is_verified:
            flash('Please verify your email address first.', 'warning')
            return redirect(url_for('auth.verify_email'))

        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()

        flash('Logged in successfully!', 'success')
        return redirect(url_for('main.index'))

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

        verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        verification_code_expiry = datetime.utcnow() + timedelta(hours=24)

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method='sha256'),
            verification_code=verification_code,
            verification_code_expiry=verification_code_expiry
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            send_verification_email(email, verification_code)
            flash('Registration successful! Please check your email for verification code.', 'success')
            return redirect(url_for('auth.verify_email'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@auth.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        code = request.form.get('code')
        user = User.query.filter_by(verification_code=code).first()

        if not user:
            flash('Invalid verification code.', 'error')
            return redirect(url_for('auth.verify_email'))

        if user.verification_code_expiry < datetime.utcnow():
            flash('Verification code has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.verify_email'))

        user.is_verified = True
        user.verification_code = None
        user.verification_code_expiry = None
        db.session.commit()

        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/verify_email.html')

@auth.route('/resend-verification', methods=['POST'])
def resend_verification():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        flash('Email not found.', 'error')
        return redirect(url_for('auth.verify_email'))

    if user.is_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('auth.login'))

    verification_code = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    user.verification_code = verification_code
    user.verification_code_expiry = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()

    send_verification_email(email, verification_code)
    flash('Verification email resent. Please check your inbox.', 'success')
    return redirect(url_for('auth.verify_email'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email not found.', 'error')
            return redirect(url_for('auth.forgot_password'))

        # Generate password reset token
        reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # Send password reset email
        send_reset_email(email, reset_token)
        flash('Password reset instructions sent to your email.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.reset_password', token=token))

        user.password = generate_password_hash(password, method='sha256')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash('Password reset successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))
