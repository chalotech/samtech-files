import os
import requests
from samtech import create_app, db
from samtech.models import Brand

def download_logo(url, brand_name):
    response = requests.get(url)
    if response.status_code == 200:
        filename = f"{brand_name.lower().replace(' ', '_')}.png"
        filepath = os.path.join('samtech/static/brand_icons', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return os.path.join('brand_icons', filename)
    return None

def add_brands():
    brands = [
        {
            'name': 'Samsung',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/2/24/Samsung_Logo.svg'
        },
        {
            'name': 'Apple',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg'
        },
        {
            'name': 'Xiaomi',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/2/29/Xiaomi_logo.svg'
        },
        {
            'name': 'Huawei',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/e/e8/Huawei_Logo.svg'
        },
        {
            'name': 'OnePlus',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/c/c9/OnePlus_Logo.svg'
        },
        {
            'name': 'Google',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg'
        },
        {
            'name': 'Sony',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/c/c4/Sony_logo.svg'
        },
        {
            'name': 'LG',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/2/20/LG_symbol.svg'
        }
    ]

    app = create_app()
    with app.app_context():
        for brand_info in brands:
            existing_brand = Brand.query.filter_by(name=brand_info['name']).first()
            if not existing_brand:
                icon_path = download_logo(brand_info['logo_url'], brand_info['name'])
                if icon_path:
                    brand = Brand(name=brand_info['name'], icon_path=icon_path)
                    db.session.add(brand)
        
        db.session.commit()

if __name__ == '__main__':
    add_brands()
