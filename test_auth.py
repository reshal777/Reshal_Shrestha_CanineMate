
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

from django.contrib.auth import authenticate
from accounts.models import User

# Test with a user (creating one if none exist)
email = 'testuser@example.com'
username = 'testuser'
password = 'testpassword123'

user = User.objects.filter(email=email).first()
if not user:
    user = User.objects.create_user(email=email, username=username, password=password)
    print(f"Created user: {email}")
else:
    user.set_password(password)
    user.save()
    print(f"Updated password for user: {email}")

# Try to authenticate with the new backend
authenticated_user = authenticate(email=email, password=password)

if authenticated_user:
    print(f"Successfully authenticated as {authenticated_user.email}")
else:
    print("Authentication failed.")

# Cleanup
# user.delete()
