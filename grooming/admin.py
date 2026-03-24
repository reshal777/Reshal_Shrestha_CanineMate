from django.contrib import admin
from .models import GroomingSalon, GroomingService, GroomingBooking

@admin.register(GroomingSalon)
class GroomingSalonAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'rating')
    search_fields = ('name', 'location')

@admin.register(GroomingService)
class GroomingServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price')
    search_fields = ('name',)

@admin.register(GroomingBooking)
class GroomingBookingAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'dog', 'booking_date', 'status', 'paid', 'amount', 'pidx')
    list_filter = ('status', 'paid', 'booking_date', 'salon')
    search_fields = ('user__username', 'dog__name', 'salon__name')
