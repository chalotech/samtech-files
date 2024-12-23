from PIL import Image, ImageDraw, ImageFont
import os

def create_logo(name, color):
    # Create a new image with a white background
    width = 300
    height = 100
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Use a default font
    font_size = 40
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate text size and position
    text_width = draw.textlength(name, font=font)
    text_height = font_size
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    # Draw the text
    draw.text((x, y), name, font=font, fill=color)
    
    # Save the image
    logo_dir = os.path.join('samtech/static/images/brands')
    os.makedirs(logo_dir, exist_ok=True)
    file_path = os.path.join(logo_dir, f'{name.lower()}_logo.png')
    image.save(file_path)
    print(f"Created logo for {name}")

# Create logos for brands that failed to download
brands = [
    ('itel', '#007AFF'),
    ('Infinix', '#FF6B00'),
    ('TECNO', '#00A0E9'),
    ('Huawei', '#FF0000'),
    ('OnePlus', '#F50514'),
    ('OPPO', '#1DA737')
]

for brand_name, brand_color in brands:
    create_logo(brand_name, brand_color)
