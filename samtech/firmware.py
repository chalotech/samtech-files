from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from . import db
from .models import Firmware, Brand, Payment, DownloadToken
import os
import uuid

firmware = Blueprint('firmware', __name__)

@firmware.route('/')
def index():
    """List all firmwares"""
    brands = Brand.query.all()
    firmwares = Firmware.query.filter_by(is_active=True).all()
    return render_template('firmware/index.html', brands=brands, firmwares=firmwares)

@firmware.route('/<int:id>')
def view(id):
    """View firmware details"""
    firmware = Firmware.query.get_or_404(id)
    return render_template('firmware/view.html', firmware=firmware)

@firmware.route('/<int:id>/pay')
@login_required
def pay(id):
    """Pay for firmware"""
    firmware = Firmware.query.get_or_404(id)
    
    # Check if user has already paid
    payment = Payment.query.filter_by(
        user_id=current_user.id,
        firmware_id=firmware.id,
        status='completed'
    ).first()
    
    if payment:
        return redirect(url_for('firmware.download', id=firmware.id))
        
    return render_template('payment/mpesa.html', firmware=firmware)

@firmware.route('/<int:id>/download')
@login_required
def download(id):
    """Download firmware"""
    firmware = Firmware.query.get_or_404(id)
    
    # Check if user has paid
    payment = Payment.query.filter_by(
        user_id=current_user.id,
        firmware_id=firmware.id,
        status='completed'
    ).first()
    
    if not payment:
        flash('Please pay for the firmware first.', 'warning')
        return redirect(url_for('firmware.pay', id=firmware.id))
    
    # Generate or get existing download token
    token = DownloadToken.query.filter_by(
        user_id=current_user.id,
        firmware_id=firmware.id
    ).first()
    
    if not token or token.expires_at < datetime.utcnow():
        # Create new token
        if token:
            db.session.delete(token)
            
        token = DownloadToken(
            token=str(uuid.uuid4()),
            user_id=current_user.id,
            firmware_id=firmware.id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(token)
        db.session.commit()
    
    return render_template('firmware/download.html', 
                         firmware=firmware, 
                         token=token,
                         expires_at=token.expires_at)

@firmware.route('/<int:id>/download/<token>')
def download_file(id, token):
    """Download firmware file"""
    firmware = Firmware.query.get_or_404(id)
    
    # Verify token
    token = DownloadToken.query.filter_by(
        token=token,
        firmware_id=firmware.id
    ).first()
    
    if not token or token.expires_at < datetime.utcnow():
        flash('Invalid or expired download token.', 'error')
        return redirect(url_for('firmware.view', id=firmware.id))
    
    # Get file path
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], firmware.filename)
    
    if not os.path.exists(file_path):
        flash('Firmware file not found.', 'error')
        return redirect(url_for('firmware.view', id=firmware.id))
    
    # Increment download count
    token.download_count += 1
    db.session.commit()
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=secure_filename(firmware.filename)
    )
