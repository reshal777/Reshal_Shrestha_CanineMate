import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

from accounts.models import User

admins = list(User.objects.filter(is_staff=True).values('username', 'email'))
if admins:
    print("Admin users found:")
    for admin in admins:
        print(f"  - {admin['username']} ({admin['email']})")
else:
    print("No admin users found.")
    print("\nTo create an admin user, run:")
    print("python manage.py shell")
    print(">>> from accounts.models import User")
    print(">>> User.objects.create_user(email='admin@example.com', username='admin', password='yourpassword', is_staff=True)")
