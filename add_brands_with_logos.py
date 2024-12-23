import os
import requests
from samtech import db, create_app
from samtech.models import Brand

def download_image(url, filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    return False

def add_brands():
    brands_data = [
        {
            'name': 'Samsung',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2017/06/Samsung-Logo-2.png',
            'description': 'Leading manufacturer of Android smartphones and tablets.'
        },
        {
            'name': 'Apple',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2016/10/Apple-Logo.png',
            'description': 'Manufacturer of iPhone, iPad, and other iOS devices.'
        },
        {
            'name': 'Google',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2021/05/Google-logo.png',
            'description': 'Creator of Android OS and Pixel devices.'
        },
        {
            'name': 'Huawei',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2016/12/Huawei-logo.png',
            'description': 'Global provider of smartphones and telecommunications equipment.'
        },
        {
            'name': 'Xiaomi',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2021/08/Xiaomi-logo.png',
            'description': 'Innovative manufacturer of smartphones and smart devices.'
        },
        {
            'name': 'OnePlus',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2022/09/OnePlus-Logo.png',
            'description': 'Premium Android smartphone manufacturer.'
        },
        {
            'name': 'Sony',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2017/06/Sony-Logo.png',
            'description': 'Manufacturer of Xperia smartphones and tablets.'
        },
        {
            'name': 'LG',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2017/03/LG-Logo.png',
            'description': 'Producer of innovative mobile devices and electronics.'
        },
        {
            'name': 'Motorola',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2017/04/Motorola-Logo.png',
            'description': 'Historic mobile phone manufacturer with modern Android devices.'
        },
        {
            'name': 'OPPO',
            'logo_url': 'https://1000logos.net/wp-content/uploads/2022/02/OPPO-Logo.png',
            'description': 'Innovative smartphone manufacturer with focus on camera technology.'
        },
        {
            'name': 'itel',
            'logo_url': 'https://raw.githubusercontent.com/abrahampo1/control_precios/master/public/img/itel.png',
            'description': 'Affordable smartphone manufacturer focused on emerging markets.'
        },
        {
            'name': 'Infinix',
            'logo_url': 'https://raw.githubusercontent.com/abrahampo1/control_precios/master/public/img/infinix.png',
            'description': 'Smart technology brand delivering innovative devices for young consumers.'
        },
        {
            'name': 'TECNO',
            'logo_url': 'https://raw.githubusercontent.com/abrahampo1/control_precios/master/public/img/tecno.png',
            'description': 'Premium smartphone brand known for camera innovation and stylish design.'
        }
    ]

    app = create_app()
    with app.app_context():
        # Clear existing brands
        Brand.query.delete()
        db.session.commit()

        for brand_data in brands_data:
            # Create brand logo filename
            logo_filename = f"images/brands/{brand_data['name'].lower()}_logo.png"
            full_path = os.path.join('samtech/static', logo_filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Download logo
            if download_image(brand_data['logo_url'], full_path):
                # Create brand in database
                brand = Brand(
                    name=brand_data['name'],
                    description=brand_data['description'],
                    icon_path=logo_filename
                )
                db.session.add(brand)
                print(f"Added {brand_data['name']} with logo")
            else:
                print(f"Failed to download logo for {brand_data['name']}")

        db.session.commit()
        print("All brands added successfully!")

if __name__ == '__main__':
    add_brands()
