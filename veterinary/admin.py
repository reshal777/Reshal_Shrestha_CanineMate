from django.contrib import admin
from .models import Clinic, Veterinarian, Appointment

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ('name', 'clinic', 'specialty', 'experience_years', 'is_emergency_available')
    list_filter = ('clinic', 'specialty', 'is_emergency_available')
    search_fields = ('name', 'specialty')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'user', 'dog', 'appointment_date', 'status', 'paid', 'amount', 'pidx')
    list_filter = ('status', 'paid', 'service_type', 'appointment_date')
    search_fields = ('user__username', 'dog__name', 'veterinarian__name')
