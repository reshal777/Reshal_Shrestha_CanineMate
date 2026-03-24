import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

from veterinary.models import Clinic

def update_clinics():
    clinics = Clinic.objects.all()
    count = 0
    for clinic in clinics:
        clinic.name = "CanineMate Pet Centre"
        clinic.save()
        count += 1
    print(f"Updated {count} clinics to 'CanineMate Pet Centre'")

if __name__ == '__main__':
    update_clinics()
