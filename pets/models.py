from django.db import models
from django.conf import settings

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
    
    # Adoption fields
    is_adoptable = models.BooleanField(default=False)
    is_adoption_post = models.BooleanField(default=False)  # True = posted via adoption form, not a personal dog
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_vaccinated = models.BooleanField(default=False)

    class Meta:
        db_table = 'home_dog'

    def __str__(self):
        return self.name

class AdoptionRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='adoption_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'home_adoptionrequest'

    def __str__(self):
        return f"Adoption for {self.dog.name} by {self.full_name}"

class Vaccination(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='vaccinations')
    name = models.CharField(max_length=100)
    date_administered = models.DateField()
    next_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Current', 'Current'), ('Due Soon', 'Due Soon')], default='Current')

    class Meta:
        db_table = 'home_vaccination'

    def __str__(self):
        return f"{self.name} for {self.dog.name}"

class HealthRecord(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='health_records')
    record_type = models.CharField(max_length=100)
    vet_name = models.CharField(max_length=100)
    date = models.DateField()
    notes = models.TextField()

    class Meta:
        db_table = 'home_healthrecord'

    def __str__(self):
        return f"{self.record_type} for {self.dog.name}"

class Medication(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    last_given = models.DateField()
    next_due = models.DateField()

    class Meta:
        db_table = 'home_medication'

    def __str__(self):
        return f"{self.name} for {self.dog.name}"

class Reminder(models.Model):
    REMINDER_TYPES = [
        ('Medicine', 'Medicine'),
        ('Vaccine', 'Vaccine'),
    ]
    FREQUENCY_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
    ]
    
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    reminder_time = models.TimeField()
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'home_reminder'

    def __str__(self):
        return f"{self.name} ({self.reminder_type}) for {self.dog.name}"
