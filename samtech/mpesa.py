from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from datetime import datetime
from . import db
from .models import Payment
import requests
import json
import logging

mpesa = Blueprint('mpesa', __name__)
logger = logging.getLogger(__name__)

def get_access_token():
    """Get M-Pesa access token"""
    consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
    consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')
    
    if not consumer_key or not consumer_secret:
        logger.error("M-Pesa credentials not configured")
        return None
    
    try:
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(
            url,
            auth=(consumer_key, consumer_secret),
            timeout=30
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        logger.error(f"Error getting M-Pesa access token: {str(e)}")
        return None

@mpesa.route('/stk_push', methods=['POST'])
@login_required
def stk_push():
    """Initiate STK Push"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['phone_number', 'amount', 'firmware_id']
        if not all(key in data for key in required):
            logger.error(f"Missing required fields in STK push request: {data}")
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields. Required: phone_number, amount, firmware_id'
            }), 400
        
        # Format phone number
        phone = data['phone_number']
        if phone.startswith('+254'):
            phone = phone[1:]
        elif phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone
            
        # Validate phone number format
        if not phone.isdigit() or len(phone) != 12:
            logger.error(f"Invalid phone number format: {phone}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid phone number format. Use format: 254XXXXXXXXX'
            }), 400

        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            logger.error(f"Invalid amount: {data['amount']}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid amount. Amount must be a positive number'
            }), 400
        
        # Create payment record
        payment = Payment(
            reference=f"FW{data['firmware_id']}_{current_user.id}",
            amount=amount,
            phone_number=phone,
            firmware_id=data['firmware_id'],
            user_id=current_user.id
        )
        db.session.add(payment)
        db.session.commit()
        
        # Get access token
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get M-Pesa access token")
            return jsonify({
                'status': 'error',
                'message': 'Could not initiate payment. Please try again later.'
            }), 500
        
        # Prepare STK Push request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        payload = {
            'BusinessShortCode': current_app.config['MPESA_SHORTCODE'],
            'Password': current_app.config['MPESA_PASSWORD'],
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone,
            'PartyB': current_app.config['MPESA_SHORTCODE'],
            'PhoneNumber': phone,
            'CallBackURL': current_app.config['MPESA_CALLBACK_URL'],
            'AccountReference': payment.reference,
            'TransactionDesc': f'Firmware Payment - {payment.reference}'
        }
        
        logger.info(f"Initiating STK push for payment {payment.reference}")
        
        # Make STK Push request
        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"M-Pesa API error: {response.text}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to initiate payment. Please try again.'
            }), 500
            
        response_data = response.json()
        if response_data.get('ResponseCode') != '0':
            logger.error(f"M-Pesa STK push failed: {response_data}")
            return jsonify({
                'status': 'error',
                'message': response_data.get('ResponseDescription', 'Failed to initiate payment')
            }), 400
            
        # Update payment record with CheckoutRequestID
        payment.checkout_request_id = response_data.get('CheckoutRequestID')
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Payment initiated. Please check your phone to complete payment.',
            'data': {
                'reference': payment.reference,
                'checkout_request_id': payment.checkout_request_id
            }
        })
        
    except requests.RequestException as e:
        logger.error(f"Network error during STK push: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Network error. Please try again.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error during STK push: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500

@mpesa.route('/status/<reference>', methods=['GET'])
@login_required
def payment_status(reference):
    """Check payment status"""
    try:
        payment = Payment.query.filter_by(reference=reference).first()
        
        if not payment:
            return jsonify({
                'status': 'error',
                'message': 'Payment not found'
            }), 404
            
        if payment.user_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403
            
        return jsonify({
            'status': payment.status,
            'message': payment.failure_reason if payment.status == 'failed' else None
        })
        
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred'
        }), 500

@mpesa.route('/callback', methods=['POST'])
def callback():
    """Handle M-Pesa callback"""
    try:
        data = request.get_json()
        logger.info(f"M-Pesa callback received: {json.dumps(data)}")
        
        # Get the callback data
        body = data.get('Body', {})
        result = body.get('stkCallback', {})
        
        # Get the payment using checkout request ID
        checkout_id = result.get('CheckoutRequestID')
        payment = Payment.query.filter_by(mpesa_request=checkout_id).first()
        
        if not payment:
            logger.error(f"Payment not found for checkout ID: {checkout_id}")
            return jsonify({'status': 'error'}), 404
        
        # Check if payment was successful
        if result.get('ResultCode') == 0:
            # Update payment status
            payment.status = 'completed'
            payment.completed_at = datetime.utcnow()
            
            # Get the amount paid
            items = result.get('CallbackMetadata', {}).get('Item', [])
            for item in items:
                if item.get('Name') == 'Amount':
                    payment.amount_paid = item.get('Value')
                elif item.get('Name') == 'MpesaReceiptNumber':
                    payment.mpesa_receipt = item.get('Value')
                elif item.get('Name') == 'TransactionDate':
                    payment.mpesa_date = item.get('Value')
            
            db.session.commit()
            logger.info(f"Payment {payment.reference} completed successfully")
        else:
            # Update payment status as failed
            payment.status = 'failed'
            payment.failure_reason = result.get('ResultDesc')
            db.session.commit()
            logger.error(f"Payment {payment.reference} failed: {result.get('ResultDesc')}")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        return jsonify({'status': 'error'}), 500
