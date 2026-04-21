from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import User

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get('email')
        if not identifier:
            return None
        
        try:
            # Check for both email (case-insensitive) and username (case-insensitive)
            user = User.objects.get(Q(username__iexact=identifier) | Q(email__iexact=identifier))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None
        
        if user.check_password(password):
            return user
        return None
