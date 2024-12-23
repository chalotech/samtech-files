from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from . import db, mail
from .models import User
from flask_mail import Message
import random
import string

auth = Blueprint('auth', __name__)

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    msg = Message('Email Verification',
                  sender='noreply@samtech.com',
                  recipients=[email])
    msg.body = f'Your verification code is: {code}'
    mail.send(msg)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    if not user.email_verified and not user.is_admin:
        flash('Please verify your email first.')
        return redirect(url_for('auth.verify_email'))

    login_user(user, remember=remember)
    return redirect(url_for('main.index'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(username=username).first()
    if user:
        flash('Username already exists')
        return redirect(url_for('auth.signup'))

    verification_code = generate_verification_code()
    new_user = User(email=email,
                    username=username,
                    password=generate_password_hash(password, method='scrypt'),
                    verification_code=verification_code)

    db.session.add(new_user)
    db.session.commit()

    try:
        send_verification_email(email, verification_code)
    except Exception as e:
        flash('Error sending verification email. Please contact admin.')

    return redirect(url_for('auth.verify_email'))

@auth.route('/verify-email')
def verify_email():
    return render_template('verify_email.html')

@auth.route('/verify-email', methods=['POST'])
def verify_email_post():
    code = request.form.get('code')
    user = User.query.filter_by(verification_code=code).first()

    if not user:
        flash('Invalid verification code')
        return redirect(url_for('auth.verify_email'))

    user.email_verified = True
    user.verification_code = None
    db.session.commit()

    flash('Email verified successfully!')
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
