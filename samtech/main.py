from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import db
from .models import Firmware, Brand, Payment, DownloadToken, User, Withdrawal
from datetime import datetime
import os
from sqlalchemy import func

main = Blueprint('main', __name__)

def save_icon(icon_file):
    """Save firmware icon and return the path"""
    if not icon_file:
        return None
        
    filename = secure_filename(icon_file.filename)
    icon_dir = os.path.join(current_app.root_path, 'static', 'images', 'firmware')
    os.makedirs(icon_dir, exist_ok=True)
    
    icon_path = os.path.join('images', 'firmware', filename)
    full_path = os.path.join(current_app.root_path, 'static', icon_path)
    icon_file.save(full_path)
    
    return icon_path

@main.route('/')
def index():
    brands = Brand.query.all()
    return render_template('index.html', brands=brands)

@main.route('/brand/<int:brand_id>')
def brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    firmwares = Firmware.query.filter_by(brand_id=brand_id).all()
    return render_template('brand.html', brand=brand, firmwares=firmwares)

@main.route('/firmware/<int:firmware_id>')
def firmware(firmware_id):
    firmware = Firmware.query.get_or_404(firmware_id)
    return render_template('firmware.html', firmware=firmware)

@main.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # Get statistics
    stats = {
        'firmware_count': Firmware.query.count(),
        'user_count': User.query.count(),
        'download_count': db.session.query(func.sum(Firmware.downloads)).scalar() or 0,
        'total_revenue': db.session.query(func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    }
    
    # Get data for tables
    firmwares = Firmware.query.all()
    brands = Brand.query.all()
    users = User.query.all()
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(100).all()
    
    return render_template('admin.html',
                         stats=stats,
                         firmwares=firmwares,
                         brands=brands,
                         users=users,
                         payments=payments)

@main.route('/admin/firmware/add', methods=['GET', 'POST'])
@login_required
def add_firmware():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            brand_id = request.form.get('brand_id')
            model = request.form.get('model')
            version = request.form.get('version')
            description = request.form.get('description')
            gmail_link = request.form.get('gmail_link')
            price = request.form.get('price')
            
            # Validate required fields
            if not all([brand_id, model, version, gmail_link, price]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('main.add_firmware'))
            
            # Handle icon upload
            icon_file = request.files.get('firmware_icon')
            icon_path = save_icon(icon_file) if icon_file else None
            
            # Create firmware
            firmware = Firmware(
                brand_id=brand_id,
                model=model,
                version=version,
                description=description,
                gmail_link=gmail_link,
                icon_path=icon_path,
                price=float(price),
                added_by=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(firmware)
            db.session.commit()
            
            flash('Firmware added successfully', 'success')
            return redirect(url_for('main.brand', brand_id=brand_id))
            
        except Exception as e:
            current_app.logger.error(f"Error adding firmware: {str(e)}")
            flash('Error adding firmware. Please try again.', 'error')
            db.session.rollback()
    
    brands = Brand.query.all()
    return render_template('add_firmware.html', brands=brands)

@main.route('/admin/firmware/<int:firmware_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_firmware(firmware_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    firmware = Firmware.query.get_or_404(firmware_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            brand_id = request.form.get('brand_id')
            model = request.form.get('model')
            version = request.form.get('version')
            description = request.form.get('description')
            gmail_link = request.form.get('gmail_link')
            price = request.form.get('price')
            
            # Validate required fields
            if not all([brand_id, model, version, gmail_link, price]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('main.edit_firmware', firmware_id=firmware_id))
            
            # Handle icon upload
            icon_file = request.files.get('firmware_icon')
            if icon_file:
                icon_path = save_icon(icon_file)
                if icon_path:
                    # Delete old icon if it exists
                    if firmware.icon_path:
                        old_icon_path = os.path.join(current_app.root_path, 'static', firmware.icon_path)
                        if os.path.exists(old_icon_path):
                            os.remove(old_icon_path)
                    firmware.icon_path = icon_path
            
            # Update firmware
            firmware.brand_id = brand_id
            firmware.model = model
            firmware.version = version
            firmware.description = description
            firmware.gmail_link = gmail_link
            firmware.price = float(price)
            
            db.session.commit()
            
            flash('Firmware updated successfully', 'success')
            return redirect(url_for('main.brand', brand_id=brand_id))
            
        except Exception as e:
            current_app.logger.error(f"Error updating firmware: {str(e)}")
            flash('Error updating firmware. Please try again.', 'error')
            db.session.rollback()
    
    brands = Brand.query.all()
    return render_template('edit_firmware.html', firmware=firmware, brands=brands)

@main.route('/admin/brand/add', methods=['POST'])
@login_required
def add_brand():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        name = request.form.get('name')
        if not name:
            flash('Brand name is required', 'error')
            return redirect(url_for('main.admin'))
        
        brand = Brand(name=name)
        db.session.add(brand)
        db.session.commit()
        
        flash('Brand added successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error adding brand: {str(e)}")
        flash('Error adding brand. Please try again.', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.admin'))

@main.route('/admin/brand/<int:brand_id>/edit', methods=['POST'])
@login_required
def edit_brand(brand_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        brand = Brand.query.get_or_404(brand_id)
        name = request.form.get('name')
        
        if not name:
            flash('Brand name is required', 'error')
            return redirect(url_for('main.admin'))
        
        brand.name = name
        db.session.commit()
        
        flash('Brand updated successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating brand: {str(e)}")
        flash('Error updating brand. Please try again.', 'error')
        db.session.rollback()
    
    return redirect(url_for('main.admin'))

@main.route('/download/<token>')
@login_required
def download_firmware(token):
    # Find the download token
    download_token = DownloadToken.query.filter_by(token=token).first_or_404()
    
    # Check if token is valid
    if not download_token.is_valid():
        flash('Download link has expired or has already been used', 'error')
        return redirect(url_for('main.firmware', firmware_id=download_token.firmware_id))
    
    # Mark token as used
    if not download_token.use_token():
        flash('Error processing download token', 'error')
        return redirect(url_for('main.firmware', firmware_id=download_token.firmware_id))
    
    # Increment download counter
    firmware = download_token.firmware
    firmware.downloads += 1
    db.session.commit()
    
    # Redirect to Gmail link
    return redirect(firmware.gmail_link)

@main.route('/payment/success/<int:payment_id>')
@login_required
def payment_success(payment_id):
    # Find the payment
    payment = Payment.query.filter_by(
        id=payment_id,
        user_id=current_user.id,
        status='completed'
    ).first_or_404()
    
    # Generate download token
    try:
        download_token = DownloadToken.generate_token(
            firmware_id=payment.firmware_id,
            payment_id=payment.id
        )
        
        # Create download URL
        download_url = url_for('main.download_firmware', 
                             token=download_token.token,
                             _external=True)
        
        return render_template('payment_success.html',
                             payment=payment,
                             download_url=download_url)
    except Exception as e:
        current_app.logger.error(f"Error generating download token: {str(e)}")
        flash('Error generating download link. Please contact support.', 'error')
        return redirect(url_for('main.firmware', firmware_id=payment.firmware_id))

@main.route('/pay')
@login_required
def pay():
    amount = request.args.get('amount', type=float)
    firmware_id = request.args.get('firmware_id', type=int)
    
    if not all([amount, firmware_id]):
        flash('Invalid payment request', 'error')
        return redirect(url_for('main.index'))
    
    firmware = Firmware.query.get_or_404(firmware_id)
    return render_template('pay.html',
                         amount=amount,
                         reference=f'FW{firmware_id}_{current_user.id}',
                         firmware=firmware)

@main.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Admin access required')
        return redirect(url_for('main.index'))
    
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('manage_users.html', users=users)

@main.route('/admin/verify-user/<int:user_id>')
@login_required
def verify_user(user_id):
    if not current_user.is_admin:
        flash('Admin access required')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.email_verified = True
    db.session.commit()
    flash('User verified successfully')
    return redirect(url_for('main.manage_users'))

@main.route('/admin/delete-user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Admin access required')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully')
    return redirect(url_for('main.manage_users'))

@main.route('/admin/withdrawals')
@login_required
def withdrawals():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
        
    # Get all completed payments that haven't been withdrawn
    available_payments = Payment.query.filter_by(
        status='completed',
        withdrawn=False
    ).all()
    
    # Calculate available balance
    available_balance = sum(payment.amount for payment in available_payments)
    
    # Get all payments and withdrawals for history
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(50).all()
    withdrawals = Withdrawal.query.order_by(Withdrawal.created_at.desc()).limit(50).all()
    
    return render_template('admin/withdrawals.html',
                         available_balance=available_balance,
                         payments=payments,
                         withdrawals=withdrawals)

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)
