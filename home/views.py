from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Veterinarian, Dog, Appointment, Clinic, GroomingSalon, GroomingService, GroomingBooking, Vaccination, HealthRecord, Medication
from django.contrib import messages
from datetime import datetime

def index_view(request):
    return render(request, "index.html")

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
