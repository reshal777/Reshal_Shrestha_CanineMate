from django.db import models
from django.conf import settings

class GroomingSalon(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    contact = models.CharField(max_length=20)
    rating = models.FloatField(default=0.0)
    tags = models.CharField(max_length=200, help_text="Comma separated tags, e.g. Bath, Haircut, Nail Trim")

    class Meta:
        db_table = 'home_groomingsalon'

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',')]

    def __str__(self):
        return self.name

class GroomingService(models.Model):
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=50, help_text="e.g. 45 min")
    price = models.IntegerField(help_text="Price in Rs.")

    class Meta:
        db_table = 'home_groomingservice'

    def __str__(self):
        return self.name

class GroomingBooking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='grooming_bookings')
    dog = models.ForeignKey('pets.Dog', on_delete=models.CASCADE, related_name='grooming_bookings')
    service = models.ForeignKey(GroomingService, on_delete=models.CASCADE, related_name='bookings')
    salon = models.ForeignKey(GroomingSalon, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    booking_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)
    paid = models.BooleanField(default=False)
    amount = models.IntegerField(default=500)
    pidx = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'home_groomingbooking'

    def __str__(self):
        return f"{self.service.name} for {self.dog.name} at {self.salon.name}"
