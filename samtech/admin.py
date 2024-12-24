from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request
from flask_login import login_required, current_user
from .models import Firmware, Brand
from .forms import AddFirmwareForm
from . import db
from werkzeug.utils import secure_filename
import os

admin = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin.route('/admin/firmware/add', methods=['GET', 'POST'])
@admin_required
def add_firmware():
    form = AddFirmwareForm()
    
    if form.validate_on_submit():
        try:
            # Create new firmware
            firmware = Firmware(
                model=form.model.data,
                version=form.version.data,
                description=form.description.data,
                gmail_link=form.gmail_link.data,
                price=form.price.data,
                brand_id=form.brand.data,
                added_by=current_user.id
            )
            
            # Handle icon upload if provided
            if form.icon.data:
                filename = secure_filename(form.icon.data.filename)
                icon_path = os.path.join('images', 'firmwares', filename)
                full_path = os.path.join(current_app.static_folder, icon_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Save the file
                form.icon.data.save(full_path)
                firmware.icon_path = icon_path
            
            db.session.add(firmware)
            db.session.commit()
            
            flash('Firmware added successfully!', 'success')
            return redirect(url_for('admin.manage_firmwares'))
            
        except Exception as e:
            current_app.logger.error(f"Error adding firmware: {str(e)}")
            flash('An error occurred while adding the firmware.', 'danger')
            db.session.rollback()
    
    return render_template('admin/add_firmware.html', form=form)

@admin.route('/admin/firmwares')
@admin_required
def manage_firmwares():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    firmwares = Firmware.query.order_by(Firmware.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/manage_firmwares.html', firmwares=firmwares)

@admin.route('/admin/firmware/<int:id>/delete', methods=['POST'])
@admin_required
def delete_firmware(id):
    firmware = Firmware.query.get_or_404(id)
    
    try:
        # Delete icon file if it exists
        if firmware.icon_path:
            icon_path = os.path.join(current_app.static_folder, firmware.icon_path)
            if os.path.exists(icon_path):
                os.remove(icon_path)
        
        db.session.delete(firmware)
        db.session.commit()
        flash('Firmware deleted successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting firmware: {str(e)}")
        flash('An error occurred while deleting the firmware.', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin.manage_firmwares'))
