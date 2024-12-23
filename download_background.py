import requests
import os

def download_background():
    url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&q=80"
    response = requests.get(url)
    if response.status_code == 200:
        filepath = os.path.join('samtech/static/images', 'background.jpg')
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print("Background image downloaded successfully")
    else:
        print("Failed to download background image")

if __name__ == '__main__':
    download_background()
