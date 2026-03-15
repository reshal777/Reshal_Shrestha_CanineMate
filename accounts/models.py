from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, phone=None, is_staff=False, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        if not username:
            raise ValueError("Username must be provided")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            phone=phone,
            is_staff=is_staff,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, phone=None, **extra_fields):
        return self.create_user(email, username, password=password, phone=phone, is_staff=True, **extra_fields)

class User(AbstractBaseUser):
    user_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True, help_text="Short biography")
    location = models.CharField(max_length=200, blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def get_full_name(self):
        first = self.first_name or ""
        last = self.last_name or ""
        return f"{first} {last}".strip()

    def __str__(self):
        return self.email
