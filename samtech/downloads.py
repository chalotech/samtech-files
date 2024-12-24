from flask import Blueprint, redirect, abort, current_app
from flask_login import login_required
from .models import DownloadLink
from . import db

downloads = Blueprint('downloads', __name__)

@downloads.route('/download/<token>')
@login_required
def download_firmware(token):
    """Handle one-time download links"""
    # Find the download link
    link = DownloadLink.query.filter_by(token=token).first()
    if not link:
        current_app.logger.warning(f"Invalid download token attempted: {token}")
        abort(404)
    
    # Check if link is valid
    if not link.is_valid():
        current_app.logger.warning(f"Expired or used download token attempted: {token}")
        abort(410)  # Gone - link expired or already used
    
    # Get the Gmail link
    gmail_link = link.firmware.gmail_link
    
    # Mark the link as used
    link.mark_as_used()
    
    # Redirect to the Gmail link
    return redirect(gmail_link)
