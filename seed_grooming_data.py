import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

from home.models import GroomingSalon, GroomingService

def seed_grooming():
    salon, created = GroomingSalon.objects.update_or_create(
        name="CanineMate Pet grooming",
        defaults={
            'location': 'Pokhara Lakeside',
            'contact': '+977-9801234567',
            'rating': 4.9,
            'tags': 'Bath, Haircut, Nail Trim, Ear Cleaning'
        }
    )
    if created:
        print(f"Created salon {salon}")

    services = [
        {'name': 'Full Bath', 'duration': '45 min', 'price': 800},
        {'name': 'Haircut & Styling', 'duration': '60 min', 'price': 1500},
        {'name': 'Nail Trimming', 'duration': '15 min', 'price': 300},
        {'name': 'Ear Cleaning', 'duration': '15 min', 'price': 250},
        {'name': 'Teeth Cleaning', 'duration': '20 min', 'price': 400},
        {'name': 'Full Grooming Package', 'duration': '120 min', 'price': 3000},
    ]

    for s_data in services:
        service, created = GroomingService.objects.get_or_create(
            name=s_data['name'],
            defaults={
                'duration': s_data['duration'],
                'price': s_data['price']
            }
        )
        if created:
            print(f"Created service {service}")

if __name__ == '__main__':
    seed_grooming()
