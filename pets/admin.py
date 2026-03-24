from django.contrib import admin
from .models import Dog, Vaccination, HealthRecord, Medication

@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'breed', 'gender', 'age')
    list_filter = ('gender', 'breed')
    search_fields = ('name', 'owner__username', 'owner__email')

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'dog', 'date_administered', 'next_due_date', 'status')
    list_filter = ('status', 'dog')
    search_fields = ('name', 'dog__name')

@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('record_type', 'dog', 'vet_name', 'date')
    list_filter = ('record_type', 'dog')
    search_fields = ('record_type', 'dog__name', 'vet_name')

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'dog', 'frequency', 'last_given', 'next_due')
    list_filter = ('dog',)
    search_fields = ('name', 'dog__name')
