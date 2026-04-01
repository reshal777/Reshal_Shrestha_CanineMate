import os
import requests
from django.core.files.base import ContentFile
from pets.models import Dog

dogs = Dog.objects.all()[:6]
image_urls = [
    "https://w0.peakpx.com/wallpaper/700/301/HD-wallpaper-german-shepherd-german-dog-dogs-shepherd-police-leaves-thumbnail.jpg",
    "https://images7.alphacoders.com/443/443165.jpg",
    "https://iheartdogs.com/wp-content/uploads/2024/08/Labrador-Retriever-Black-scaled.jpg",
    "https://content.lyka.com.au/f/1016262/1104x676/e36872ce32/beagle.png/m/640x427/smart/filters:format(webp)",
    "https://andreaarden.com/wp-content/uploads/2024/04/wesley-sanchez-cyimMEASu3A-unsplash-scaled.jpg",
    "https://premiumpethouse.com/public/img/dog-breeds/culture-pomeranian/culture-pomeranian9.jpg"
]

def download_image(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

for i, dog in enumerate(dogs):
    if i < len(image_urls):
        img_content = download_image(image_urls[i])
        if img_content:
            # Save the image content to the model
            ext = image_urls[i].split('.')[-1].split('?')[0] # Basic extension extraction
            if len(ext) > 4: ext = 'jpg'
            dog.image.save(f"dog_{dog.id}.{ext}", ContentFile(img_content), save=True)
            print(f"Saved image for {dog.name}")

print("All 6 dogs now have beautiful images!")
