from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'username', 'phone')
    ordering = ('email',)
    fields = ('email', 'username', 'phone', 'password', 'is_staff', 'is_active')
