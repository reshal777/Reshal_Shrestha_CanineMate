from django.db import models
from django.conf import settings

class Clinic(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    class Meta:
        db_table = 'home_clinic'

    def __str__(self):
        return f"{self.name} - {self.location}"

class Veterinarian(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vet_profile')
    name = models.CharField(max_length=100)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='veterinarians')
    rating = models.FloatField(default=0.0)
    specialty = models.CharField(max_length=100, default="General Veterinary Medicine")
    experience_years = models.IntegerField(default=5)
    about = models.TextField(blank=True, null=True)
    expertise = models.TextField(blank=True, null=True, help_text="Comma separated areas of expertise")
    education = models.TextField(blank=True, null=True, help_text="Comma separated education details")
    achievements = models.TextField(blank=True, null=True, help_text="Comma separated achievements")
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    consultation_fee = models.IntegerField(default=1000)
    languages = models.CharField(max_length=200, default="Nepali, English")
    image = models.ImageField(upload_to='vets/', blank=True, null=True)
    is_emergency_available = models.BooleanField(default=False)
    initial = models.CharField(max_length=1, blank=True)

    class Meta:
        db_table = 'home_veterinarian'

    @property
    def expertise_list(self):
        return [x.strip() for x in self.expertise.split(',')] if self.expertise else []

    @property
    def education_list(self):
        return [x.strip() for x in self.education.split(',')] if self.education else []

    @property
    def achievement_list(self):
        return [x.strip() for x in self.achievements.split(',')] if self.achievements else []

    def save(self, *args, **kwargs):
        if not self.initial and self.name:
            self.initial = self.name[0].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.clinic.name})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    SERVICE_CHOICES = [
        ('Regular Checkup', 'Regular Checkup'),
        ('Vaccination', 'Vaccination'),
        ('Emergency', 'Emergency'),
        ('Follow-up', 'Follow-up'),
        ('Consultation', 'Consultation'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    dog = models.ForeignKey('pets.Dog', on_delete=models.CASCADE, related_name='appointments')
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, related_name='appointments')
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    paid = models.BooleanField(default=False)
    amount = models.IntegerField(default=1000)
    pidx = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'home_appointment'

    def __str__(self):
        return f"{self.service_type} for {self.dog.name} with {self.veterinarian.name}"
