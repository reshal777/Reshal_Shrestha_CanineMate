import os
import django
import sys

# Add project root to path
sys.path.append('d:/FYP Code/CanineMate')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

from shop.models import Product

def seed_products():
    products_data = [
        {
            'name': 'Premium Dog Food',
            'category': 'Food',
            'price': 2500,
            'old_price': 3200,
            'discount_percent': 22,
            'rating': 4.5,
            'reviews_count': 120,
            'stock': 50,
            'description': 'High-quality nutritious dog food for healthy pets.',
            'image_url': 'https://m.media-amazon.com/images/I/71WuWI0+VxL.jpg'
        },
        {
            'name': 'Interactive Dog Toy',
            'category': 'Toys',
            'price': 850,
            'old_price': 1000,
            'discount_percent': 15,
            'rating': 4.8,
            'reviews_count': 85,
            'stock': 30,
            'description': 'Keeps your dog engaged and active for hours.',
            'image_url': 'https://armorthepooch.ca/cdn/shop/products/TotallyPooched-Huff_nPuffRubberBall_StickSet3pc2.webp?v=1681950681&width=2400'
        },
        {
            'name': 'Leather Dog Collar',
            'category': 'Accessories',
            'price': 1200,
            'old_price': 1500,
            'discount_percent': 20,
            'rating': 4.6,
            'reviews_count': 64,
            'stock': 20,
            'description': 'Durable and stylish genuine leather collar.',
            'image_url': 'https://assets.mgimgs.com/mgimgs/rk/images/dp/wcm/202542/0002/carson-leather-dog-collar-2-o.jpg'
        },
        {
            'name': 'Dog Shampoo Set',
            'category': 'Health & Wellness',
            'price': 950,
            'old_price': 1200,
            'discount_percent': 21,
            'rating': 4.7,
            'reviews_count': 45,
            'stock': 15,
            'description': 'Gentle shampoo set for a clean and shiny coat.',
            'image_url': 'https://www.hugglepets.co.uk/wp-content/uploads/2023/11/Sampoo-and-Cologne4455.png'
        },
        {
            'name': 'Organic Dog Treats',
            'category': 'Food',
            'price': 650,
            'old_price': 800,
            'discount_percent': 18,
            'rating': 4.9,
            'reviews_count': 210,
            'stock': 100,
            'description': 'Organic, grain-free treats your pet will love.',
            'image_url': 'https://tastythriftytimely.com/wp-content/uploads/2023/01/3-Ingredient-Dog-Treats-Featured.jpg'
        },
        {
            'name': 'Plush Toy Bundle',
            'category': 'Toys',
            'price': 1100,
            'old_price': 1400,
            'discount_percent': 21,
            'rating': 4.4,
            'reviews_count': 32,
            'stock': 12,
            'description': 'A bundle of soft toys for cuddling and play.',
            'image_url': 'https://www.worldofbears.com/wp-content/uploads/2023/10/pic_600_91974.jpg'
        }
    ]

    for p_data in products_data:
        product, created = Product.objects.update_or_create(
            name=p_data['name'],
            defaults={
                'category': p_data['category'],
                'price': p_data['price'],
                'old_price': p_data.get('old_price'),
                'discount_percent': p_data.get('discount_percent', 0),
                'rating': p_data['rating'],
                'reviews_count': p_data['reviews_count'],
                'stock': p_data['stock'],
                'description': p_data['description'],
            }
        )
        if created:
            print(f"Created product: {p_data['name']}")
        else:
            print(f"Product already exists: {p_data['name']}")

if __name__ == "__main__":
    seed_products()
