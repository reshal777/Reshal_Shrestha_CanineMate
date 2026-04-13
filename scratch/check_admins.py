import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
# Add current directory to path
import sys
sys.path.append(os.getcwd())

django.setup()

from accounts.models import User

# List all staff/superuser emails
admins = User.objects.filter(is_staff=True)
if admins:
    print("Found following admin/staff emails:")
    for admin in admins:
        print(f" - {admin.email}")
else:
    print("No staff users found.")
