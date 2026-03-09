from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Veterinarian, Dog, Appointment, Clinic, GroomingSalon, GroomingService, GroomingBooking, Vaccination, HealthRecord, Medication, ChatMessage
from django.contrib import messages
from django.db.models import Q
from accounts.models import User
from datetime import datetime
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def index_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
        
    vets = Veterinarian.objects.all()[:4]
    if not vets.exists():
        clinic = Clinic.objects.create(name="Canine Mate Clinic", location="Kathmandu")
        v1 = Veterinarian.objects.create(name="Dr. Rajesh Sharma", clinic=clinic, experience_years=15, specialty="Chief Veterinarian", about="Expert in general veterinary medicine and emergency care.")
        v2 = Veterinarian.objects.create(name="Sita Thapa", clinic=clinic, experience_years=10, specialty="Head Groomer", about="Certified pet groomer.")
        v3 = Veterinarian.objects.create(name="Hari Gurung", clinic=clinic, experience_years=5, specialty="Adoption Coordinator", about="Passionate rescuer.")
        vets = Veterinarian.objects.all()[:4]
    return render(request, "index.html", {'vets': vets})

def adoption_listing_view(request):
    return render(request, "adoptionlisting.html")

def contact_us_view(request):
    return render(request, "contactus.html")

def shop_view(request):
    return render(request, "shop.html")

def cart_view(request):
    return render(request, "cart.html")

def product_details_view(request, product_id=None):
    return render(request, "productdetails.html")

def checkout_view(request):
    return render(request, "checkout.html")

@login_required
def doctor_profile_view(request, vet_id):
    vet = get_object_or_404(Veterinarian, id=vet_id)
    dogs = Dog.objects.filter(owner=request.user)
    return render(request, "doctorprofile.html", {"vet": vet, "dogs": dogs})

@login_required
def dog_profile_view(request, dog_id=None):
    dogs = Dog.objects.filter(owner=request.user)
    
    if not dogs.exists():
        # Optional: create a demo dog for first-time users
        Dog.objects.create(owner=request.user, name="Buddy", breed="Golden Retriever", age="3 years", gender="Male", weight="32 kg", color="Golden")
        dogs = Dog.objects.filter(owner=request.user)
    
    if dog_id:
        dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
    else:
        dog = dogs.first()

    vaccinations = dog.vaccinations.all()
    health_records = dog.health_records.all()
    medications = dog.medications.all()

    context = {
        'dogs': dogs,
        'dog': dog,
        'vaccinations': vaccinations,
        'health_records': health_records,
        'medications': medications,
    }
    return render(request, "dogprofile.html", context)

@login_required
def add_dog(request):
    if request.method == "POST":
        name = request.POST.get('name')
        breed = request.POST.get('breed')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        weight = request.POST.get('weight')
        color = request.POST.get('color')
        image = request.FILES.get('image')
        
        dog = Dog.objects.create(
            owner=request.user,
            name=name,
            breed=breed,
            age=age,
            gender=gender,
            weight=weight,
            color=color,
            image=image
        )
        messages.success(request, f"{dog.name} added successfully!")
        return redirect('dogprofile', dog_id=dog.id)
    return redirect('dogprofile')

@login_required
def edit_dog(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
    if request.method == "POST":
        dog.name = request.POST.get('name')
        dog.breed = request.POST.get('breed')
        dog.age = request.POST.get('age')
        dog.gender = request.POST.get('gender')
        dog.weight = request.POST.get('weight')
        dog.color = request.POST.get('color')
        if request.FILES.get('image'):
            dog.image = request.FILES.get('image')
        dog.save()
        messages.success(request, f"{dog.name}'s profile updated!")
        return redirect('dogprofile', dog_id=dog.id)
    return redirect('dogprofile', dog_id=dog.id)

@login_required
def delete_dog(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
    dog.delete()
    messages.success(request, "Dog profile deleted.")
    return redirect('dogprofile')

@login_required
def add_vaccination(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
    if request.method == "POST":
        name = request.POST.get('name')
        date_administered = request.POST.get('date_administered')
        next_due_date = request.POST.get('next_due_date')
        status = request.POST.get('status', 'Current')
        
        Vaccination.objects.create(
            dog=dog,
            name=name,
            date_administered=date_administered,
            next_due_date=next_due_date,
            status=status
        )
        messages.success(request, "Vaccination record added!")
    return redirect('dogprofile', dog_id=dog.id)

@login_required
def edit_vaccination(request, vaccination_id):
    vaccination = get_object_or_404(Vaccination, id=vaccination_id, dog__owner=request.user)
    if request.method == "POST":
        vaccination.name = request.POST.get('name')
        vaccination.date_administered = request.POST.get('date_administered')
        vaccination.next_due_date = request.POST.get('next_due_date')
        vaccination.status = request.POST.get('status')
        vaccination.save()
        messages.success(request, "Vaccination record updated!")
    return redirect('dogprofile', dog_id=vaccination.dog.id)

@login_required
def add_health_record(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
    if request.method == "POST":
        record_type = request.POST.get('record_type')
        vet_name = request.POST.get('vet_name')
        date = request.POST.get('date')
        notes = request.POST.get('notes')
        
        HealthRecord.objects.create(
            dog=dog,
            record_type=record_type,
            vet_name=vet_name,
            date=date,
            notes=notes
        )
        messages.success(request, "Health record added!")
    return redirect('dogprofile', dog_id=dog.id)

@login_required
def delete_health_record(request, record_id):
    record = get_object_or_404(HealthRecord, id=record_id, dog__owner=request.user)
    dog_id = record.dog.id
    record.delete()
    messages.success(request, "Health record deleted.")
    return redirect('dogprofile', dog_id=dog_id)

def medicine_reminder_view(request):
    return render(request, "medicinereminder.html")

@login_required
def vet_appointment_view(request):
    if request.method == "POST":
        dog_id = request.POST.get('dog')
        vet_id = request.POST.get('vet')
        service_type = request.POST.get('service_type')
        date = request.POST.get('date')
        time = request.POST.get('time')
        notes = request.POST.get('notes', '')

        dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
        vet = get_object_or_404(Veterinarian, id=vet_id)

        Appointment.objects.create(
            user=request.user,
            dog=dog,
            veterinarian=vet,
            service_type=service_type,
            appointment_date=date,
            appointment_time=time,
            notes=notes,
            status='Confirmed'
        )
        messages.success(request, "Appointment booked successfully!")
        return redirect('vetappointment')

    # GET request logic
    # Fetch confirmed appointments only
    appointments = Appointment.objects.filter(user=request.user, status='Confirmed').order_by('appointment_date', 'appointment_time')
    
    # Fetch veterinarians sorted by rating
    veterinarians = Veterinarian.objects.all().order_by('-rating')
    
    # Fetch user's dogs
    dogs = Dog.objects.filter(owner=request.user)
    
    # Ensure there are dogs for the user for the demo
    if not dogs.exists():
        # Let's create dummy dog for the demo purpose if requested user exists
        Dog.objects.create(owner=request.user, name="Buddy", breed="Golden Retriever")
        Dog.objects.create(owner=request.user, name="Max", breed="Golden Retriever")
        dogs = Dog.objects.filter(owner=request.user)

    context = {
        'appointments': appointments,
        'veterinarians': veterinarians,
        'dogs': dogs,
        'no_vets': not veterinarians.exists(),
    }
    return render(request, "vetappoinment.html", context)

@login_required
def reschedule_appointment(request, appointment_id):
    if request.method == "POST":
        appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        new_date = request.POST.get('date')
        new_time = request.POST.get('time')
        
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.save()
        messages.success(request, "Appointment rescheduled successfully!")
        return redirect('vetappointment')
    return redirect('vetappointment')

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    appointment.status = 'Cancelled'
    appointment.save()
    messages.success(request, "Appointment cancelled successfully!")
    return redirect('vetappointment')

@login_required
def grooming_booking_view(request):
    if request.method == "POST":
        dog_id = request.POST.get('dog')
        service_id = request.POST.get('service')
        date = request.POST.get('date')
        time = request.POST.get('time')
        notes = request.POST.get('notes', '')

        dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
        service = get_object_or_404(GroomingService, id=service_id)
        salon = GroomingSalon.objects.first()

        GroomingBooking.objects.create(
            user=request.user,
            dog=dog,
            service=service,
            salon=salon,
            booking_date=date,
            booking_time=time,
            notes=notes,
            status='Confirmed'
        )
        messages.success(request, "Grooming booking confirmed successfully!")
        return redirect('groomingbooking')

    # GET request logic
    bookings = GroomingBooking.objects.filter(user=request.user, status='Confirmed').order_by('booking_date', 'booking_time')
    services = GroomingService.objects.all()
    salon = GroomingSalon.objects.first()
    dogs = Dog.objects.filter(owner=request.user)
    
    context = {
        'bookings': bookings,
        'services': services,
        'salon': salon,
        'dogs': dogs,
        'no_services': not services.exists(),
    }
    return render(request, "groomingbooking.html", context)

@login_required
def reschedule_grooming(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(GroomingBooking, id=booking_id, user=request.user)
        new_date = request.POST.get('date')
        new_time = request.POST.get('time')
        
        booking.booking_date = new_date
        booking.booking_time = new_time
        booking.save()
        messages.success(request, "Grooming booking rescheduled successfully!")
        return redirect('groomingbooking')
    return redirect('groomingbooking')

@login_required
def cancel_grooming(request, booking_id):
    booking = get_object_or_404(GroomingBooking, id=booking_id, user=request.user)
    booking.status = 'Cancelled'
    booking.save()
    messages.success(request, "Grooming booking cancelled successfully!")
    return redirect('groomingbooking')

@login_required
def chat_room_view(request, user_id):
    other_user = get_object_or_404(User, user_id=user_id)
    # Get all messages between current user and other user
    chat_messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    context = {
        'other_user': other_user,
        'chat_messages': chat_messages,
    }
    return render(request, "chat.html", context)

@login_required
def chat_list_view(request):
    # Get all unique users the current user has chatted with
    sent_to = ChatMessage.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received_from = ChatMessage.objects.filter(receiver=request.user).values_list('sender', flat=True)
    user_ids = set(list(sent_to) + list(received_from))
    chat_users = User.objects.filter(user_id__in=user_ids)
    return render(request, "chat_list.html", {'chat_users': chat_users})

@login_required
def user_profile_view(request):
    """Display user profile page"""
    user = request.user
    dogs = Dog.objects.filter(owner=user)
    appointments = Appointment.objects.filter(user=user, status='Confirmed').order_by('-appointment_date')[:5]
    grooming_bookings = GroomingBooking.objects.filter(user=user, status='Confirmed').order_by('-booking_date')[:5]
    
    # Calculate recent activities
    activities = []
    for appt in appointments[:3]:
        activities.append({
            'action': f"Booked appointment with {appt.veterinarian.name}",
            'date': appt.appointment_date.strftime('%b %d, %Y') if appt.appointment_date else 'N/A'
        })
    
    context = {
        'user': user,
        'dogs': dogs,
        'dogs_count': dogs.count(),
        'appointments_count': appointments.count(),
        'activities': activities,
    }
    return render(request, "userprofile.html", context)

@login_required
@csrf_exempt
def get_user_profile_api(request):
    """API endpoint to get user profile data"""
    if request.method == "GET":
        user = request.user
        dogs = Dog.objects.filter(owner=user)
        appointments = Appointment.objects.filter(user=user, status='Confirmed').count()
        grooming_bookings = GroomingBooking.objects.filter(user=user, status='Confirmed').count()
        
        from payment.models import Order
        try:
            orders = Order.objects.filter(user=user).count()
        except:
            orders = 0
        
        profile_data = {
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'phone': user.phone or '',
            'location': user.location or '',
            'bio': user.bio or '',
            'joinedDate': user.date_joined.strftime('%B %d, %Y') if user.date_joined else 'N/A',
            'dogs': [
                {
                    'id': dog.id,
                    'name': dog.name,
                    'breed': dog.breed or 'Unknown',
                    'age': dog.age or 'N/A',
                    'image': dog.image.url if dog.image else 'https://via.placeholder.com/300x300?text=No+Image'
                }
                for dog in dogs
            ],
            'stats': {
                'dogs': dogs.count(),
                'appointments': appointments,
                'orders': orders,
                'bookings': grooming_bookings,
            }
        }
        return JsonResponse(profile_data)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def update_user_profile_api(request):
    """API endpoint to update user profile"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Update user fields
            if 'first_name' in data:
                user.first_name = data.get('first_name', user.first_name)
            if 'last_name' in data:
                user.last_name = data.get('last_name', user.last_name)
            if 'phone' in data:
                user.phone = data.get('phone', user.phone)
            if 'location' in data:
                user.location = data.get('location', user.location)
            if 'bio' in data:
                user.bio = data.get('bio', user.bio)
            
            user.save()
            messages.success(request, "Profile updated successfully!")
            
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully',
                'user': {
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'phone': user.phone or '',
                    'location': user.location or '',
                    'bio': user.bio or '',
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def chatbot_proxy(request):
    import os
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message")
            
            # Groq API Configuration
            # Update this key with your active API key or set GROQ_API_KEY environment variable
            api_key = os.environ.get("GROQ_API_KEY", "gsk_VPhf8Xl8PzPr0W4X7XlWWGdyb3FY0RnU")
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are CanineMate Assistant, a helpful AI focused on dog care, health, and services in Nepal. You are friendly, knowledgeable, and sometimes use dog-themed puns like 'ruff', 'paws-itive', etc. Keep answers concise and helpful."
                    },
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                bot_response = result['choices'][0]['message']['content']
                return JsonResponse({"response": bot_response})
            elif response.status_code == 401 or response.status_code == 403:
                return JsonResponse({"error": "I couldn't connect because the Groq API Key is missing or invalid! Please update `api_key` in `views.py` with your active key. 🐾"}, status=401)
            else:
                return JsonResponse({"error": f"API Error: {response.text}"}, status=response.status_code)
                
        except requests.exceptions.Timeout:
            return JsonResponse({"error": "The connection timed out. Please try again in a moment! 🐾"}, status=504)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)} 🐾"}, status=500)
            
    return JsonResponse({"error": "Invalid request"}, status=400)
