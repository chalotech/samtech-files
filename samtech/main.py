from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user
from . import db
from .models import Brand, Firmware, User, Payment, Withdrawal
from werkzeug.utils import secure_filename
from .mpesa import payment_status
import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    brands = Brand.query.all()
    return render_template('index.html', brands=brands)

@main.route('/brand/<int:brand_id>')
def brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    firmwares = Firmware.query.filter_by(brand_id=brand_id).order_by(Firmware.created_at.desc()).all()
    return render_template('brand.html', brand=brand, firmwares=firmwares)

@main.route('/add-firmware/<int:brand_id>', methods=['GET', 'POST'])
@login_required
def add_firmware(brand_id):
    if not current_user.is_admin:
        flash('Admin access required')
        return redirect(url_for('main.index'))
    
    brand = Brand.query.get_or_404(brand_id)
    
    if request.method == 'POST':
        model = request.form.get('model')
        version = request.form.get('version')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        firmware_file = request.files.get('firmware_file')
        firmware_icon = request.files.get('firmware_icon')
        
        if firmware_file:
            filename = secure_filename(firmware_file.filename)
            file_path = os.path.join('static/firmware_files', filename)
            firmware_file.save(os.path.join('samtech', file_path))
            
            icon_path = None
            if firmware_icon:
                icon_filename = secure_filename(firmware_icon.filename)
                icon_path = os.path.join('static/firmware_icons', icon_filename)
                os.makedirs(os.path.join('samtech/static/firmware_icons'), exist_ok=True)
                firmware_icon.save(os.path.join('samtech', icon_path))
            
            firmware = Firmware(
                model=model,
                version=version,
                description=description,
                file_path=file_path,
                icon_path=icon_path,
                price=price,
                brand_id=brand_id,
                added_by=current_user.id
            )
            
            db.session.add(firmware)
            db.session.commit()
            flash('Firmware added successfully')
            return redirect(url_for('main.brand', brand_id=brand_id))
    
    return render_template('add_firmware.html', brand=brand)

@main.route('/edit-firmware/<int:firmware_id>', methods=['GET', 'POST'])
@login_required
def edit_firmware(firmware_id):
    if not current_user.is_admin:
        flash('Admin access required')
        return redirect(url_for('main.index'))
    
    firmware = Firmware.query.get_or_404(firmware_id)
    
    if request.method == 'POST':
        firmware.model = request.form.get('model')
        firmware.version = request.form.get('version')
        firmware.description = request.form.get('description')
        firmware.price = float(request.form.get('price', 0))
        
        firmware_file = request.files.get('firmware_file')
        firmware_icon = request.files.get('firmware_icon')
        
        if firmware_file:
            filename = secure_filename(firmware_file.filename)
            file_path = os.path.join('static/firmware_files', filename)
            firmware_file.save(os.path.join('samtech', file_path))
            firmware.file_path = file_path
            
        if firmware_icon:
            icon_filename = secure_filename(firmware_icon.filename)
            icon_path = os.path.join('static/firmware_icons', icon_filename)
            os.makedirs(os.path.join('samtech/static/firmware_icons'), exist_ok=True)
            firmware_icon.save(os.path.join('samtech', icon_path))
            firmware.icon_path = icon_path
        
        db.session.commit()
        flash('Firmware updated successfully')
        return redirect(url_for('main.brand', brand_id=firmware.brand_id))
    
    return render_template('edit_firmware.html', firmware=firmware)

@main.route('/delete-firmware/<int:firmware_id>')
@login_required
def delete_firmware(firmware_id):
    if not current_user.is_admin:
        flash('Admin access required')
        return redirect(url_for('main.index'))
    
    firmware = Firmware.query.get_or_404(firmware_id)
    brand_id = firmware.brand_id
    
    try:
        os.remove(os.path.join('samtech', firmware.file_path))
    except:
        pass
    
    db.session.delete(firmware)
    db.session.commit()
    flash('Firmware deleted successfully')
    return redirect(url_for('main.brand', brand_id=brand_id))

@main.route('/pay')
@login_required
def pay():
    amount = request.args.get('amount', type=float)
    firmware_id = request.args.get('firmware_id', type=int)
    
    if not amount or not firmware_id:
        flash('Invalid payment request', 'danger')
        return redirect(url_for('main.index'))
    
    firmware = Firmware.query.get_or_404(firmware_id)
    
    return render_template('payment.html', 
                         amount=amount,
                         reference=f'FW{firmware_id}_{current_user.id}',
                         firmware=firmware)

@main.route('/download/<int:firmware_id>')
@login_required
def download_firmware(firmware_id):
    firmware = Firmware.query.get_or_404(firmware_id)
    
    # Check if firmware is free
    if firmware.price == 0:
        return process_download(firmware)
        
    # Check if payment was successful
    reference = f'FW{firmware_id}_{current_user.id}'
    payment = payment_status.get(reference, {})
    
    if payment.get('completed'):
        return process_download(firmware)
    else:
        flash('Payment required to download this firmware', 'warning')
        return redirect(url_for('main.pay', amount=firmware.price, firmware_id=firmware.id))

def process_download(firmware):
    """Process firmware download"""
    if not firmware.file_path:
        flash('Firmware file not available', 'danger')
        return redirect(url_for('main.brand', brand_id=firmware.brand_id))
        
    file_path = os.path.join('samtech', 'static', firmware.file_path)
    if not os.path.exists(file_path):
        flash('Firmware file not found', 'danger')
        return redirect(url_for('main.brand', brand_id=firmware.brand_id))
    
    # Increment download count
    firmware.downloads += 1
    db.session.commit()
    
    # Return file for download
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{firmware.model}_v{firmware.version}.bin"
    )

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
