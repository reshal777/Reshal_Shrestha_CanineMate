from django.utils import timezone
from datetime import timedelta
from veterinary.models import Appointment
from grooming.models import GroomingBooking
from pets.models import Vaccination, Medication, Dog

def notifications(request):
    notifications = []
    
    if request.user.is_authenticated:
        now = timezone.now()
        today = now.date()
        upcoming_limit = today + timedelta(days=7) # Look ahead 7 days for most items
        
        # 1. Upcoming Appointments
        appointments = Appointment.objects.filter(
            user=request.user, 
            status='Confirmed',
            appointment_date__gte=today,
            appointment_date__lte=today + timedelta(days=30)
        ).order_by('appointment_date')
        
        for appt in appointments:
            days_away = (appt.appointment_date - today).days
            time_str = appt.appointment_time.strftime('%I:%M %p')
            if days_away == 0:
                dt_str = f"Today at {time_str}"
            elif days_away == 1:
                dt_str = f"Tomorrow at {time_str}"
            else:
                dt_str = f"In {days_away} days at {time_str}"
                
            notifications.append({
                'title': 'Vet Appointment',
                'message': f"{appt.service_type} for {appt.dog.name} with {appt.veterinarian.name}",
                'time': dt_str,
                'type': 'appointment',
                'sort_date': appt.appointment_date
            })
            
        # 2. Upcoming Grooming
        grooming = GroomingBooking.objects.filter(
            user=request.user, 
            status='Confirmed',
            booking_date__gte=today,
            booking_date__lte=today + timedelta(days=30)
        ).order_by('booking_date')
        
        for book in grooming:
            days_away = (book.booking_date - today).days
            time_str = book.booking_time.strftime('%I:%M %p')
            if days_away == 0:
                dt_str = f"Today at {time_str}"
            elif days_away == 1:
                dt_str = f"Tomorrow at {time_str}"
            else:
                dt_str = f"In {days_away} days at {time_str}"
                
            notifications.append({
                'title': 'Grooming Appointment',
                'message': f"{book.service.name} for {book.dog.name} at {book.salon.name}",
                'time': dt_str,
                'type': 'grooming',
                'sort_date': book.booking_date
            })
            
        # 3. Vaccinations Due
        user_dogs = Dog.objects.filter(owner=request.user)
        vaccinations = Vaccination.objects.filter(
            dog__in=user_dogs,
            next_due_date__gte=today,
            next_due_date__lte=today + timedelta(days=30)
        ).order_by('next_due_date')
        
        for vac in vaccinations:
            days_away = (vac.next_due_date - today).days
            if days_away == 0:
                dt_str = "Due Today!"
            elif days_away == 1:
                dt_str = "Due Tomorrow"
            else:
                dt_str = f"Due in {days_away} days"
                
            notifications.append({
                'title': 'Vaccination Due',
                'message': f"{vac.name} for {vac.dog.name}",
                'time': dt_str,
                'type': 'vaccination',
                'sort_date': vac.next_due_date
            })
            
        # 4. Medication Reminders
        medications = Medication.objects.filter(
            dog__in=user_dogs,
            next_due__gte=today,
            next_due__lte=today + timedelta(days=7)
        ).order_by('next_due')
        
        for med in medications:
            days_away = (med.next_due - today).days
            if days_away == 0:
                dt_str = "Due Today!"
            elif days_away == 1:
                dt_str = "Due Tomorrow"
            else:
                dt_str = f"Due in {days_away} days"
                
            notifications.append({
                'title': 'Medicine Reminder',
                'message': f"{med.name} for {med.dog.name} ({med.frequency})",
                'time': dt_str,
                'type': 'medication',
                'sort_date': med.next_due
            })
            
        # 5. New Unified Reminders
        from pets.models import Reminder
        reminders = Reminder.objects.filter(
            dog__in=user_dogs,
            is_active=True,
            start_date__gte=today,
            start_date__lte=today + timedelta(days=30)
        ).order_by('start_date')
        
        for rem in reminders:
            days_away = (rem.start_date - today).days
            time_str = rem.reminder_time.strftime('%I:%M %p')
            
            if days_away == 0:
                dt_str = f"Due Today at {time_str}!"
            elif days_away == 1:
                dt_str = f"Tomorrow at {time_str}"
            else:
                dt_str = f"Due in {days_away} days"
                
            notifications.append({
                'title': f"{rem.reminder_type} Alert",
                'message': f"{rem.name} for {rem.dog.name}",
                'time': dt_str,
                'type': rem.reminder_type.lower(),
                'sort_date': rem.start_date
            })
            
        # Sort by date closest to today
        notifications.sort(key=lambda x: x['sort_date'])
        
        # Limit to top 10 notifications
        notifications = notifications[:10]

    return {
        'user_notifications': notifications,
        'notification_count': len(notifications)
    }
def global_context(request):
    from shop.models import CartItem
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()
    return {
        'cart_count': cart_count
    }
