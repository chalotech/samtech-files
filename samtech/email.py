from flask import current_app, render_template
from flask_mail import Message
from datetime import datetime
from . import mail

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

def send_reset_email(email, token):
    msg = Message('Reset Your Samtech Firmware Password',
                  sender=('Samtech Firmware', 'chalomtech4@gmail.com'),
                  recipients=[email])
    
    msg.html = render_template('email/reset_password.html',
                             user={'username': email.split('@')[0]},
                             token=token,
                             now=datetime.utcnow())
    
    try:
        mail.send(msg)
        current_app.logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        raise
