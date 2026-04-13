import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

from shop.models import Product

def update_all_ratings():
    products = Product.objects.all()
    print(f"Updating ratings for {products.count()} products...")
    for product in products:
        product.update_rating()
    print("Update complete.")

if __name__ == "__main__":
    update_all_ratings()
