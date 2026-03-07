from django.db import models
from django.conf import settings

class Clinic(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

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

class Dog(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dogs')
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, blank=True, null=True)
    age = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    weight = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='dog_profiles/', blank=True, null=True)
    microchip_id = models.CharField(max_length=100, blank=True, null=True)
    special_needs = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Vaccination(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='vaccinations')
    name = models.CharField(max_length=100)
    date_administered = models.DateField()
    next_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Current', 'Current'), ('Due Soon', 'Due Soon')], default='Current')

    def __str__(self):
        return f"{self.name} for {self.dog.name}"

class HealthRecord(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='health_records')
    record_type = models.CharField(max_length=100)
    vet_name = models.CharField(max_length=100)
    date = models.DateField()
    notes = models.TextField()

    def __str__(self):
        return f"{self.record_type} for {self.dog.name}"

class Medication(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    last_given = models.DateField()
    next_due = models.DateField()

    def __str__(self):
        return f"{self.name} for {self.dog.name}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    SERVICE_CHOICES = [
        ('Regular Checkup', 'Regular Checkup'),
        ('Vaccination', 'Vaccination'),
        ('Emergency', 'Emergency'),
        ('Follow-up', 'Follow-up'),
        ('Consultation', 'Consultation'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='appointments')
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, related_name='appointments')
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Confirmed')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.service_type} for {self.dog.name} with {self.veterinarian.name}"

class GroomingSalon(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    contact = models.CharField(max_length=20)
    rating = models.FloatField(default=0.0)
    tags = models.CharField(max_length=200, help_text="Comma separated tags, e.g. Bath, Haircut, Nail Trim")

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',')]

    def __str__(self):
        return self.name

class GroomingService(models.Model):
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=50, help_text="e.g. 45 min")
    price = models.IntegerField(help_text="Price in Rs.")

    def __str__(self):
        return self.name

class GroomingBooking(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='grooming_bookings')
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='grooming_bookings')
    service = models.ForeignKey(GroomingService, on_delete=models.CASCADE, related_name='bookings')
    salon = models.ForeignKey(GroomingSalon, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    booking_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Confirmed')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.service.name} for {self.dog.name} at {self.salon.name}"

class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.message[:20]}"
