import requests
import os

url = "https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"
js_dir = r"d:\FYP Code\CanineMate\static\js"
js_path = os.path.join(js_dir, "lucide.min.js")

if not os.path.exists(js_dir):
    os.makedirs(js_dir)

print(f"Downloading Lucide from {url}...")
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    with open(js_path, "wb") as f:
        f.write(response.content)
    print(f"Successfully saved Lucide to {js_path}")
except Exception as e:
    print(f"Error downloading Lucide: {e}")
