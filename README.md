# Samtech Files

A web application for managing and selling firmware files with M-Pesa integration.

## Features

- User Authentication
- Email Verification
- Admin Dashboard
- Firmware Management
- M-Pesa Payment Integration
- Payment History
- Admin Withdrawals

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/samtech-files.git
cd samtech-files
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
SECRET_KEY=your-secret-key-here

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# M-Pesa Configuration
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=your-shortcode
MPESA_PASSKEY=your-passkey
MPESA_CALLBACK_URL=your-callback-url
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
python run.py
```

## Usage

1. Create an admin account:
   - Default admin credentials:
     - Email: samtech@admin.com
     - Password: samuel

2. Add firmware files:
   - Log in as admin
   - Go to Brands section
   - Add brands and firmware files

3. Process payments:
   - Users can purchase firmware using M-Pesa
   - Admins can withdraw funds through the admin dashboard

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
