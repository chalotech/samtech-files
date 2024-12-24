from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import requests
import base64
import json
import os
from . import db
from .models import Payment, Withdrawal, DownloadLink
from flask_mail import Message
from . import mail

mpesa = Blueprint('mpesa', __name__)

# Dictionary to store payment status
payment_status = {}

class MpesaClient:
    def __init__(self):
        self.env = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.shortcode = os.getenv('MPESA_SHORTCODE')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL')
        
        if self.env == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
        
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        """Get OAuth access token from Safaricom"""
        url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        auth = base64.b64encode(f'{self.consumer_key}:{self.consumer_secret}'.encode()).decode()
        
        try:
            response = requests.get(
                url,
                headers={'Authorization': f'Basic {auth}'}
            )
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            print(f'Error getting access token: {str(e)}')
            return None

    def is_configured(self):
        return all([self.consumer_key, self.consumer_secret, self.shortcode, self.passkey, self.callback_url])

    def stk_push(self, phone_number, amount, reference):
        """Initiate STK push payment"""
        if not self.is_configured():
            return {'error': 'M-Pesa is not properly configured. Please set up your shortcode and other credentials.'}
            
        if not self.access_token:
            return {'error': 'Could not get access token'}

        # Format phone number (remove leading 0 or +254)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f'{self.shortcode}{self.passkey}{timestamp}'.encode()).decode()

        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),  # Ensure amount is an integer
            'PartyA': phone_number,
            'PartyB': self.shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': reference,
            'TransactionDesc': f'Payment for {reference}'
        }

        print(f"Sending STK push request with payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(
                f'{self.base_url}/mpesa/stkpush/v1/processrequest',
                json=payload,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            # Store merchant request ID for callback matching
            if 'MerchantRequestID' in result:
                payment_status[reference]['merchant_request_id'] = result['MerchantRequestID']
                
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"Error initiating STK push: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f"\nResponse: {e.response.text}"
            print(error_msg)
            return {'error': error_msg}

    def b2c_payment(self, phone_number, amount, remarks="Withdrawal"):
        """Initiate B2C payment (Business to Customer)"""
        if not self.access_token:
            return {'error': 'Could not get access token'}

        # Format phone number (remove leading 0 or +254)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f'{self.shortcode}{self.passkey}{timestamp}'.encode()).decode()

        payload = {
            'InitiatorName': 'testapi',  # For sandbox testing
            'SecurityCredential': self.passkey,  # In production, this should be encrypted
            'CommandID': 'BusinessPayment',
            'Amount': int(amount),
            'PartyA': self.shortcode,
            'PartyB': phone_number,
            'Remarks': remarks,
            'QueueTimeOutURL': f'{self.callback_url}/timeout',
            'ResultURL': f'{self.callback_url}/result',
            'Occasion': 'Withdrawal'
        }

        try:
            response = requests.post(
                f'{self.base_url}/mpesa/b2c/v1/paymentrequest',
                json=payload,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            print(f"B2C Response status code: {response.status_code}")
            print(f"B2C Response content: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error initiating B2C payment: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f"\nResponse: {e.response.text}"
            print(error_msg)
            return {'error': error_msg}

# Initialize M-Pesa client
mpesa_client = MpesaClient()

@mpesa.route('/initiate', methods=['POST'])
def initiate_payment():
    """Initiate M-Pesa STK push payment"""
    data = request.get_json()
    
    if not all(k in data for k in ['phone', 'amount', 'reference']):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Initialize payment status
    payment_status[data['reference']] = {'completed': False, 'failed': False}
    
    result = mpesa_client.stk_push(
        phone_number=data['phone'],
        amount=int(data['amount']),
        reference=data['reference']
    )
    
    return jsonify(result)

@mpesa.route('/b2c', methods=['POST'])
def initiate_b2c_payment():
    """Initiate M-Pesa B2C payment"""
    data = request.get_json()
    
    if not all(k in data for k in ['phone', 'amount']):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    result = mpesa_client.b2c_payment(
        phone_number=data['phone'],
        amount=int(data['amount']),
        remarks=data.get('remarks', 'Withdrawal')
    )
    
    return jsonify(result)

@mpesa.route('/callback', methods=['POST'])
def callback():
    """Handle M-Pesa callback"""
    data = request.get_json()
    
    # Extract callback data
    result_code = data.get('ResultCode')
    reference = data.get('MerchantRequestID')
    
    # Find the payment
    payment = Payment.query.filter_by(reference=reference).first()
    if not payment:
        current_app.logger.error(f"Payment not found for reference: {reference}")
        return jsonify({'status': 'error', 'message': 'Payment not found'}), 404
    
    if result_code == 0:  # Success
        # Update payment status
        payment.status = 'completed'
        payment.completed_at = datetime.utcnow()
        
        # Create download link
        download_link = DownloadLink.create_for_payment(payment)
        
        # Generate download URL
        download_url = request.host_url.rstrip('/') + '/download/' + download_link.token
        
        # Send email with download link
        try:
            msg = Message(
                'Your Firmware Download Link',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[payment.user.email]
            )
            msg.body = f'''Thank you for your payment!

Your firmware download is ready. Click the link below to download:
{download_url}

Note: This link will expire in 24 hours and can only be used once.

Best regards,
Samtech Team'''
            
            mail.send(msg)
            current_app.logger.info(f"Download link email sent to {payment.user.email}")
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Payment completed'})
    else:
        # Update payment status to failed
        payment.status = 'failed'
        db.session.commit()
        return jsonify({'status': 'error', 'message': 'Payment failed'}), 400

@mpesa.route('/status/<reference>', methods=['GET'])
def check_status(reference):
    """Check payment status"""
    payment = Payment.query.filter_by(reference=reference).first()
    if not payment:
        return jsonify({'status': 'error', 'message': 'Payment not found'}), 404
    
    return jsonify({
        'status': payment.status,
        'reference': payment.reference,
        'amount': float(payment.amount),
        'created_at': payment.created_at.isoformat(),
        'completed_at': payment.completed_at.isoformat() if payment.completed_at else None
    })

@mpesa.route('/result', methods=['POST'])
def b2c_result():
    """Handle M-Pesa B2C result"""
    data = request.get_json()
    
    # Extract withdrawal details from result data
    result = data.get('Result', {})
    transaction_id = result.get('TransactionID')
    
    # Find withdrawal by transaction ID
    withdrawal = Withdrawal.query.filter_by(transaction_id=transaction_id).first()
    if withdrawal:
        result_code = result.get('ResultCode', 1)
        if result_code == 0:
            withdrawal.status = 'completed'
            withdrawal.completed_at = datetime.utcnow()
            
            # Mark related payments as withdrawn
            payments = Payment.query.filter_by(
                status='completed',
                withdrawn=False
            ).limit(withdrawal.amount).all()
            
            total_amount = 0
            for payment in payments:
                if total_amount + payment.amount <= withdrawal.amount:
                    payment.withdrawn = True
                    total_amount += payment.amount
                else:
                    break
        else:
            withdrawal.status = 'failed'
            withdrawal.error_message = result.get('ResultDesc', 'Withdrawal failed')
        
        db.session.commit()
    
    return jsonify({'status': 'success'})

@mpesa.route('/timeout', methods=['POST'])
def b2c_timeout():
    """Handle M-Pesa B2C timeout"""
    # Log timeout event
    print("B2C timeout occurred")
    return jsonify({'status': 'timeout'})
