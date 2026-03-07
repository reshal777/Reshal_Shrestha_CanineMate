import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

from home.models import Clinic, Veterinarian

def seed():
    clinics = [
        {'name': 'Nepal Vet Clinic', 'location': 'Pokhara Lakeside'},
        {'name': 'Pet Care Center', 'location': 'Pokhara Lakeside'},
        {'name': 'Animal Hospital', 'location': 'Pokhara Lakeside'},
        {'name': 'Vet Wellness', 'location': 'Pokhara Lakeside'},
    ]

    for c_data in clinics:
        clinic, created = Clinic.objects.update_or_create(name=c_data['name'], defaults={'location': c_data['location']})
        if created:
            print(f"Created clinic {clinic}")

    vets = [
        {'name': 'Dr. Sharma', 'clinic_name': 'Nepal Vet Clinic', 'rating': 4.8},
        {'name': 'Dr. Thapa', 'clinic_name': 'Pet Care Center', 'rating': 4.9},
        {'name': 'Dr. Gurung', 'clinic_name': 'Animal Hospital', 'rating': 4.7},
        {'name': 'Dr. Rai', 'clinic_name': 'Vet Wellness', 'rating': 4.6},
    ]

    for v_data in vets:
        clinic = Clinic.objects.get(name=v_data['clinic_name'])
        vet, created = Veterinarian.objects.get_or_create(
            name=v_data['name'],
            clinic=clinic,
            defaults={'rating': v_data['rating']}
        )
        if created:
            print(f"Created vet {vet}")

if __name__ == '__main__':
    seed()
