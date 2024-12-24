from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import db
from .models import Brand, Firmware, User, Payment
import os
from datetime import datetime, timedelta
from PIL import Image
import uuid
import csv
from io import StringIO, BytesIO
from openpyxl import Workbook

admin = Blueprint('admin', __name__, url_prefix='/admin')

def save_logo(file):
    """Save brand logo and return the file path"""
    if not file:
        return None
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    
    # Create brands directory if it doesn't exist
    logos_dir = os.path.join(current_app.static_folder, 'images', 'brands')
    os.makedirs(logos_dir, exist_ok=True)
    
    filepath = os.path.join(logos_dir, unique_filename)
    
    # Save and optimize image
    try:
        image = Image.open(file)
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        # Resize if too large while maintaining aspect ratio
        if max(image.size) > 800:
            image.thumbnail((800, 800))
        # Save with optimization
        image.save(filepath, optimize=True, quality=85)
        return os.path.join('images', 'brands', unique_filename)
    except Exception as e:
        current_app.logger.error(f"Error saving logo: {str(e)}")
        return None

@admin.route('/brands')
@login_required
def manage_brands():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    brands = Brand.query.order_by(Brand.name).all()
    return render_template('admin/brands.html', brands=brands)

@admin.route('/brands/add', methods=['POST'])
@login_required
def add_brand():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    logo = request.files.get('logo')
    
    if not name:
        flash('Brand name is required.', 'error')
        return redirect(url_for('admin.manage_brands'))
    
    # Check if brand already exists
    if Brand.query.filter_by(name=name).first():
        flash('A brand with this name already exists.', 'error')
        return redirect(url_for('admin.manage_brands'))
    
    # Save logo if provided
    logo_path = save_logo(logo) if logo else None
    
    try:
        brand = Brand(name=name, description=description, logo=logo_path)
        db.session.add(brand)
        db.session.commit()
        flash('Brand added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding brand: {str(e)}")
        flash('An error occurred while adding the brand.', 'error')
    
    return redirect(url_for('admin.manage_brands'))

@admin.route('/brands/<int:id>/edit', methods=['POST'])
@login_required
def edit_brand(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    brand = Brand.query.get_or_404(id)
    name = request.form.get('name')
    description = request.form.get('description')
    logo = request.files.get('logo')
    
    if not name:
        flash('Brand name is required.', 'error')
        return redirect(url_for('admin.manage_brands'))
    
    try:
        # Check if new name conflicts with other brands
        existing = Brand.query.filter(Brand.name == name, Brand.id != id).first()
        if existing:
            flash('A brand with this name already exists.', 'error')
            return redirect(url_for('admin.manage_brands'))
        
        # Update logo if new one provided
        if logo and logo.filename:
            new_logo_path = save_logo(logo)
            if new_logo_path:
                # Delete old logo if it exists
                if brand.logo:
                    old_logo_path = os.path.join(current_app.static_folder, brand.logo)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)
                brand.logo = new_logo_path
        
        brand.name = name
        brand.description = description
        db.session.commit()
        flash('Brand updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating brand: {str(e)}")
        flash('An error occurred while updating the brand.', 'error')
    
    return redirect(url_for('admin.manage_brands'))

@admin.route('/brands/<int:id>/delete', methods=['POST'])
@login_required
def delete_brand(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    brand = Brand.query.get_or_404(id)
    
    try:
        # Delete logo file if it exists
        if brand.logo:
            logo_path = os.path.join(current_app.static_folder, brand.logo)
            if os.path.exists(logo_path):
                os.remove(logo_path)
        
        db.session.delete(brand)
        db.session.commit()
        flash('Brand deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting brand: {str(e)}")
        flash('An error occurred while deleting the brand.', 'error')
    
    return redirect(url_for('admin.manage_brands'))

@admin.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query based on filters
    query = User.query
    
    # Search filter
    search = request.args.get('search', '')
    if search:
        query = query.filter(User.email.ilike(f'%{search}%'))
    
    # Status filter
    status = request.args.get('status', 'all')
    if status == 'verified':
        query = query.filter_by(is_verified=True)
    elif status == 'unverified':
        query = query.filter_by(is_verified=False)
    elif status == 'admin':
        query = query.filter_by(is_admin=True)
    
    # Sort order
    sort = request.args.get('sort', 'newest')
    if sort == 'newest':
        query = query.order_by(User.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(User.created_at.asc())
    elif sort == 'email':
        query = query.order_by(User.email.asc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page)
    users = pagination.items
    
    return render_template('admin/users.html', users=users, pagination=pagination)

@admin.route('/users/<int:id>')
@login_required
def get_user(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(id)
    return jsonify({
        'id': user.id,
        'email': user.email,
        'is_verified': user.is_verified,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'downloads_count': len(user.downloads),
        'payments_count': len(user.payments)
    })

@admin.route('/users/<int:id>/toggle-admin', methods=['POST'])
@login_required
def toggle_admin(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    
    # Prevent removing admin from last admin user
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot remove admin privileges from the last admin user.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f"Admin privileges {'granted to' if user.is_admin else 'removed from'} {user.email}", 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/users/<int:id>/verify', methods=['POST'])
@login_required
def verify_user(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    user.is_verified = True
    user.verification_code = None
    user.verification_code_expiry = None
    db.session.commit()
    
    flash(f'User {user.email} has been verified.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    
    # Prevent deleting the last admin user
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the last admin user.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.email} has been deleted.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/users/export', methods=['POST'])
@login_required
def export_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    format = request.form.get('format', 'csv')
    date_range = request.form.get('range', 'all')
    fields = request.form.getlist('fields')
    
    # Build query based on date range
    query = User.query
    if date_range == 'today':
        query = query.filter(User.created_at >= datetime.utcnow().date())
    elif date_range == 'week':
        query = query.filter(User.created_at >= datetime.utcnow() - timedelta(days=7))
    elif date_range == 'month':
        query = query.filter(User.created_at >= datetime.utcnow() - timedelta(days=30))
    elif date_range == 'year':
        query = query.filter(User.created_at >= datetime.utcnow() - timedelta(days=365))
    
    users = query.all()
    
    if format == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = []
        if 'email' in fields: header.append('Email')
        if 'status' in fields: header.append('Status')
        if 'joined' in fields: header.append('Join Date')
        if 'downloads' in fields: header.append('Downloads')
        if 'payments' in fields: header.append('Payments')
        writer.writerow(header)
        
        # Write data
        for user in users:
            row = []
            if 'email' in fields: row.append(user.email)
            if 'status' in fields: row.append('Verified' if user.is_verified else 'Pending')
            if 'joined' in fields: row.append(user.created_at.strftime('%Y-%m-%d'))
            if 'downloads' in fields: row.append(len(user.downloads))
            if 'payments' in fields: row.append(len(user.payments))
            writer.writerow(row)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'users_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    elif format == 'excel':
        output = BytesIO()
        workbook = Workbook()
        worksheet = workbook.active
        
        # Write header
        header = []
        if 'email' in fields: header.append('Email')
        if 'status' in fields: header.append('Status')
        if 'joined' in fields: header.append('Join Date')
        if 'downloads' in fields: header.append('Downloads')
        if 'payments' in fields: header.append('Payments')
        worksheet.append(header)
        
        # Write data
        for user in users:
            row = []
            if 'email' in fields: row.append(user.email)
            if 'status' in fields: row.append('Verified' if user.is_verified else 'Pending')
            if 'joined' in fields: row.append(user.created_at.strftime('%Y-%m-%d'))
            if 'downloads' in fields: row.append(len(user.downloads))
            if 'payments' in fields: row.append(len(user.payments))
            worksheet.append(row)
        
        workbook.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'users_{datetime.utcnow().strftime("%Y%m%d")}.xlsx'
        )

@admin.route('/firmware')
@login_required
def manage_firmware():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    firmwares = Firmware.query.order_by(Firmware.name).all()
    brands = Brand.query.order_by(Brand.name).all()
    return render_template('admin/firmware.html', firmwares=firmwares, brands=brands)

@admin.route('/firmware/add', methods=['POST'])
@login_required
def add_firmware():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Get form data
        name = request.form.get('name')
        version = request.form.get('version')
        description = request.form.get('description')
        features = request.form.get('features')
        brand_id = request.form.get('brand_id')
        price = request.form.get('price')
        
        # Validate required fields
        if not all([name, version, description, brand_id, price]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('admin.manage_firmware'))
        
        # Handle file uploads
        firmware_file = request.files.get('firmware_file')
        image = request.files.get('image')
        
        if not firmware_file:
            flash('Firmware file is required.', 'error')
            return redirect(url_for('admin.manage_firmware'))
        
        # Save firmware file
        firmware_filename = secure_filename(firmware_file.filename)
        unique_firmware_filename = f"{uuid.uuid4()}_{firmware_filename}"
        firmware_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_firmware_filename)
        firmware_file.save(firmware_path)
        
        # Save image if provided
        image_path = None
        if image:
            image_filename = secure_filename(image.filename)
            unique_image_filename = f"{uuid.uuid4()}_{image_filename}"
            images_dir = os.path.join(current_app.static_folder, 'images', 'firmware')
            os.makedirs(images_dir, exist_ok=True)
            image_path = os.path.join(images_dir, unique_image_filename)
            
            # Optimize image
            img = Image.open(image)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            if max(img.size) > 800:
                img.thumbnail((800, 800))
            img.save(image_path, optimize=True, quality=85)
            image_path = os.path.join('images', 'firmware', unique_image_filename)
        
        # Create firmware record
        firmware = Firmware(
            name=name,
            version=version,
            description=description,
            features=features,
            filename=unique_firmware_filename,
            image=image_path,
            size=os.path.getsize(firmware_path),
            price=float(price),
            brand_id=int(brand_id),
            creator_id=current_user.id,
            is_active=True
        )
        
        db.session.add(firmware)
        db.session.commit()
        flash('Firmware added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding firmware: {str(e)}")
        flash('An error occurred while adding the firmware.', 'error')
        if os.path.exists(firmware_path):
            os.remove(firmware_path)
        if image_path and os.path.exists(os.path.join(current_app.static_folder, image_path)):
            os.remove(os.path.join(current_app.static_folder, image_path))
    
    return redirect(url_for('admin.manage_firmware'))

@admin.route('/firmware/<int:id>/edit', methods=['POST'])
@login_required
def edit_firmware(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    firmware = Firmware.query.get_or_404(id)
    
    try:
        # Update basic info
        firmware.name = request.form.get('name')
        firmware.version = request.form.get('version')
        firmware.description = request.form.get('description')
        firmware.features = request.form.get('features')
        firmware.brand_id = int(request.form.get('brand_id'))
        firmware.price = float(request.form.get('price'))
        
        # Handle firmware file update
        firmware_file = request.files.get('firmware_file')
        if firmware_file:
            # Delete old file
            old_firmware_path = os.path.join(current_app.config['UPLOAD_FOLDER'], firmware.filename)
            if os.path.exists(old_firmware_path):
                os.remove(old_firmware_path)
            
            # Save new file
            firmware_filename = secure_filename(firmware_file.filename)
            unique_firmware_filename = f"{uuid.uuid4()}_{firmware_filename}"
            firmware_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_firmware_filename)
            firmware_file.save(firmware_path)
            
            firmware.filename = unique_firmware_filename
            firmware.size = os.path.getsize(firmware_path)
        
        # Handle image update
        image = request.files.get('image')
        if image:
            # Delete old image
            if firmware.image:
                old_image_path = os.path.join(current_app.static_folder, firmware.image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image
            image_filename = secure_filename(image.filename)
            unique_image_filename = f"{uuid.uuid4()}_{image_filename}"
            images_dir = os.path.join(current_app.static_folder, 'images', 'firmware')
            os.makedirs(images_dir, exist_ok=True)
            image_path = os.path.join(images_dir, unique_image_filename)
            
            # Optimize image
            img = Image.open(image)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            if max(img.size) > 800:
                img.thumbnail((800, 800))
            img.save(image_path, optimize=True, quality=85)
            firmware.image = os.path.join('images', 'firmware', unique_image_filename)
        
        db.session.commit()
        flash('Firmware updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating firmware: {str(e)}")
        flash('An error occurred while updating the firmware.', 'error')
    
    return redirect(url_for('admin.manage_firmware'))

@admin.route('/firmware/<int:id>/delete', methods=['POST'])
@login_required
def delete_firmware(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    firmware = Firmware.query.get_or_404(id)
    
    try:
        # Delete firmware file
        firmware_path = os.path.join(current_app.config['UPLOAD_FOLDER'], firmware.filename)
        if os.path.exists(firmware_path):
            os.remove(firmware_path)
        
        # Delete image if exists
        if firmware.image:
            image_path = os.path.join(current_app.static_folder, firmware.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(firmware)
        db.session.commit()
        flash('Firmware deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting firmware: {str(e)}")
        flash('An error occurred while deleting the firmware.', 'error')
    
    return redirect(url_for('admin.manage_firmware'))

@admin.route('/firmware/<int:id>')
@login_required
def get_firmware(id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Access denied'})
    
    firmware = Firmware.query.get_or_404(id)
    return jsonify({
        'status': 'success',
        'firmware': {
            'name': firmware.name,
            'version': firmware.version,
            'description': firmware.description,
            'features': firmware.features,
            'brand_id': firmware.brand_id,
            'price': firmware.price
        }
    })
