import requests
import os

def download_background():
    # Using a phone collection image that matches your provided image
    url = "https://images.unsplash.com/photo-1616348436168-de43ad0db179?w=1920&q=80"
    response = requests.get(url)
    if response.status_code == 200:
        filepath = os.path.join('samtech/static/images', 'phones_background.jpg')
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print("Phones background image downloaded successfully")
    else:
        print("Failed to download phones background image")

if __name__ == '__main__':
    download_background()
