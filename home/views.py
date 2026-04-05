from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from pets.models import Dog, Vaccination, HealthRecord, Medication, Reminder
from veterinary.models import Clinic, Veterinarian, Appointment
from grooming.models import GroomingSalon, GroomingService, GroomingBooking
from shop.models import Product, Order, CartItem, OrderItem
from chat.models import ChatMessage
from django.contrib import messages
from django.db.models import Q
from accounts.models import User
from datetime import datetime
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from payment.khalti_utils import initiate_khalti_payment, verify_khalti_payment
from .email_utils import send_order_email, send_appointment_email, send_grooming_email

def index_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
        
    vets = Veterinarian.objects.exclude(specialty__icontains='Grooming')[:4]
    if not vets.exists():
        clinic = Clinic.objects.create(name="CanineMate Pet Centre", location="Kathmandu")
        v1 = Veterinarian.objects.create(name="Dr. Rajesh Sharma", clinic=clinic, experience_years=15, specialty="Chief Veterinarian", about="Expert in general veterinary medicine and emergency care.")
        v2 = Veterinarian.objects.create(name="Sita Thapa", clinic=clinic, experience_years=10, specialty="Head Groomer", about="Certified pet groomer.")
        v3 = Veterinarian.objects.create(name="Hari Gurung", clinic=clinic, experience_years=5, specialty="Adoption Coordinator", about="Passionate rescuer.")
        vets = Veterinarian.objects.all()[:4]
    return render(request, "index.html", {'vets': vets})

def adoption_listing_view(request):
    breed_filter = request.GET.get('breed', 'All Breeds')
    age_filter = request.GET.get('age', 'All Ages')
    location_filter = request.GET.get('location', 'All Locations')
    
    dogs = Dog.objects.filter(is_adoptable=True)
    
    if breed_filter != 'All Breeds':
        dogs = dogs.filter(breed__iexact=breed_filter)
        
    if age_filter != 'All Ages':
        if 'Puppy' in age_filter:
            dogs = dogs.filter(age__icontains='6 months') # Simplified check, usually it would be comparison with actual birthday
        elif 'Young' in age_filter:
            # We'll do a simple contains check for common terms for now
            dogs = dogs.filter(Q(age__icontains='1 year') | Q(age__icontains='2 years'))
        elif 'Adult' in age_filter:
            # Check for ages beyond 3
            dogs = dogs.exclude(age__icontains='months').exclude(age__icontains='1 year').exclude(age__icontains='2 years')
            
    if location_filter != 'All Locations':
        dogs = dogs.filter(location__iexact=location_filter)
        
    breeds = Dog.objects.filter(is_adoptable=True).values_list('breed', flat=True).distinct()
    locations = Dog.objects.filter(is_adoptable=True).values_list('location', flat=True).distinct()
    
    context = {
        'dogs': dogs,
        'dog_count': dogs.count(),
        'breeds': breeds,
        'locations': locations,
        'current_breed': breed_filter,
        'current_age': age_filter,
        'current_location': location_filter,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "adoption_list_partial.html", context)

    return render(request, "adoptionlisting.html", context)

@login_required
def post_adoption_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        breed = request.POST.get('breed')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        weight = request.POST.get('weight')
        color = request.POST.get('color')
        
        description = request.POST.get('description')
        location = request.POST.get('location')
        is_vaccinated = request.POST.get('is_vaccinated') == 'on'
        microchip_id = request.POST.get('microchip_id')
        special_needs = request.POST.get('special_needs')
        
        image = request.FILES.get('image')
        
        # Create Dog with adoptable flag set to True
        dog = Dog.objects.create(
            owner=request.user,
            name=name,
            breed=breed,
            age=age,
            gender=gender,
            weight=weight,
            color=color,
            description=description,
            location=location,
            is_vaccinated=is_vaccinated,
            microchip_id=microchip_id,
            special_needs=special_needs,
            image=image,
            is_adoptable=True,
            is_adoption_post=True
        )
        
        messages.success(request, f"Successfully posted {dog.name} for adoption!")
        return redirect('adoption')
        
    return render(request, "Postadoption.html")

@login_required
def edit_adoption_view(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id, owner=request.user, is_adoptable=True)
    if request.method == "POST":
        dog.name = request.POST.get('name')
        dog.breed = request.POST.get('breed')
        dog.age = request.POST.get('age')
        dog.gender = request.POST.get('gender')
        dog.weight = request.POST.get('weight')
        dog.color = request.POST.get('color')
        
        dog.description = request.POST.get('description')
        dog.location = request.POST.get('location')
        dog.is_vaccinated = request.POST.get('is_vaccinated') == 'on'
        
        if request.FILES.get('image'):
            dog.image = request.FILES.get('image')
            
        dog.save()
        messages.success(request, f"Adoption post for {dog.name} updated!")
        return redirect('adoption')
        
    return render(request, "Postadoption.html", {"dog": dog})

@login_required
def delete_adoption_view(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id, owner=request.user, is_adoptable=True)
    name = dog.name
    dog.delete()
    messages.success(request, f"Adoption post for {name} has been deleted.")
    return redirect('adoption')

@login_required
def adopt_dog_view(request, dog_id):
    if request.method == "POST":
        dog = get_object_or_404(Dog, id=dog_id, is_adoptable=True)
        
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        reason = request.POST.get('reason')
        
        # Check if already submitted a request
        if AdoptionRequest.objects.filter(dog=dog, user=request.user, status='Pending').exists():
            messages.warning(request, f"You already have a pending request for {dog.name}.")
            return redirect('adoptionlisting')

        AdoptionRequest.objects.create(
            dog=dog,
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            reason=reason
        )
        messages.success(request, f"Your adoption request for {dog.name} has been submitted! We will contact you soon.")
        return redirect('adoptionlisting')
        
    return redirect('adoptionlisting')

def contact_us_view(request):
    return render(request, "contactus.html")

@login_required
def user_settings_view(request):
    """User settings page"""
    return render(request, "usersetting.html")

def about_us_view(request):
    vets = Veterinarian.objects.exclude(specialty__icontains='Grooming')[:4]
    return render(request, "Aboutus.html", {'vets': vets})


def shop_view(request):
    category_filter = request.GET.get('category')
    price_range = request.GET.get('price_range')
    search_query = request.GET.get('search')
    
    products = Product.objects.all().order_by('-id')
    
    if category_filter:
        products = products.filter(category=category_filter)
        
    if price_range:
        if price_range == 'under_500':
            products = products.filter(price__lt=500)
        elif price_range == '500_1000':
            products = products.filter(price__gte=500, price__lte=1000)
        elif price_range == '1000_2000':
            products = products.filter(price__gte=1000, price__lte=2000)
        elif price_range == 'above_2000':
            products = products.filter(price__gt=2000)
            
    if search_query:
        products = products.filter(name__icontains=search_query)
            
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    context = {
        'products': products,
        'categories': categories,
        'product_count': products.count(),
        'current_price_range': price_range,
        'current_category': category_filter,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "shop_product_list.html", context)
        
    return render(request, "shop.html", context)

def cart_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.total_price for item in cart_items)
    return render(request, "cart.html", {'cart_items': cart_items, 'total': total})

@login_required
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.GET.get('qty', 1))
    
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
        
    cart_item.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': CartItem.objects.filter(user=request.user).count()})

    messages.success(request, f"Added {product.name} to your cart!")
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('shop')

@login_required
def remove_from_cart_view(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')

@login_required
def update_cart_quantity_view(request, item_id):
    """AJAX endpoint to increment/decrement quantity on the cart page."""
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    delta = int(request.GET.get('delta', 1))
    
    if item.quantity + delta >= 1:
        item.quantity += delta
        item.save()
        
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(i.total_price for i in cart_items)
    delivery = 0 if subtotal >= 3000 else 150
    total = subtotal + delivery
    
    return JsonResponse({
        'success': True,
        'quantity': item.quantity,
        'item_total': float(item.total_price),
        'subtotal': float(subtotal),
        'delivery': delivery,
        'total': float(total)
    })

def product_details_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:5]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, "productdetails.html", context)

@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('shop')
        
    total_amount = sum(item.total_price for item in cart_items)
    
    if request.method == "POST":
        payment_method = request.POST.get('payment_method', 'Cash on Delivery')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        
        # Create the order
        order = Order.objects.create(
            user=request.user,
            amount=int(total_amount),
            payment_method=payment_method,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            postal_code=postal_code,
            status='Pending'
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # If Khalti, initiate payment
        if payment_method.lower() == 'khalti':
            amount_paisa = int(total_amount * 100)
            return_url = request.build_absolute_uri(reverse('khalti_callback'))
            website_url = request.build_absolute_uri('/')
            
            customer_info = {
                "name": f"{first_name} {last_name}",
                "email": email,
                "phone": phone or "9800000000"
            }
            
            from payment.khalti_utils import initiate_khalti_payment
            response = initiate_khalti_payment(
                amount=amount_paisa,
                purchase_order_id=f"ORD-{order.id}",
                purchase_order_name=f"Order {order.order_id}",
                return_url=return_url,
                website_url=website_url,
                customer_info=customer_info
            )
            
            if "payment_url" in response:
                order.pidx = response['pidx']
                order.save()
                return redirect(response['payment_url'])
            else:
                error_msg = response.get('detail') or response.get('error_key') or 'Unknown error'
                messages.error(request, f"Khalti initiation failed: {error_msg}")
                return redirect('checkout')
        else:
            # Cash on Delivery
            # Update Product Sales and Stock
            for cart_item in cart_items:
                product = cart_item.product
                product.sales += cart_item.quantity
                product.stock -= cart_item.quantity
                product.save()
            
            cart_items.delete()
            send_order_email(order)
            messages.success(request, "Order placed successfully! We will contact you soon for delivery.")
            return render(request, "payment_success.html", {
                "message": "Your order has been placed successfully! 🐾",
                "redirect_url": "pet_expenses",
                "button_text": "View Product"
            })

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, "checkout.html", context)

@login_required
def doctor_profile_view(request, vet_id):
    vet = get_object_or_404(Veterinarian, id=vet_id)
    dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)
    return render(request, "doctorprofile.html", {"vet": vet, "dogs": dogs})

@login_required
def dog_profile_view(request, dog_id=None):
    dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)
    
    if not dogs.exists():
        # Optional: create a demo dog for first-time users
        Dog.objects.create(owner=request.user, name="Buddy", breed="Golden Retriever", age="3 years", gender="Male", weight="32 kg", color="Golden")
        dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)
    
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

@login_required
def medicine_reminder_view(request):
    dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)
    reminders = Reminder.objects.filter(dog__owner=request.user).order_by('start_date', 'reminder_time')
    
    # Segmenting for the template
    medicine_reminders = reminders.filter(reminder_type='Medicine')
    vaccine_reminders = reminders.filter(reminder_type='Vaccine')
    
    # Upcoming this week (next 7 days)
    from datetime import date, timedelta
    from django.utils import timezone
    now = timezone.now()
    today = now.date()
    now_time = now.time()
    next_week = today + timedelta(days=7)
    upcoming_this_week = reminders.filter(
        Q(start_date__gt=today) | Q(start_date=today, reminder_time__gte=now_time),
        is_active=True,
        start_date__lte=next_week
    )[:5]
    
    context = {
        'dogs': dogs,
        'medicine_reminders': medicine_reminders,
        'vaccine_reminders': vaccine_reminders,
        'upcoming_this_week': upcoming_this_week,
    }
    return render(request, "medicinereminder.html", context)

@login_required
def add_reminder(request):
    if request.method == "POST":
        dog_id = request.POST.get('dog')
        reminder_type = request.POST.get('reminder_type')
        name = request.POST.get('name')
        frequency = request.POST.get('frequency')
        time = request.POST.get('time')
        start_date = request.POST.get('start_date')
        
        dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
        
        from pets.models import Reminder
        Reminder.objects.create(
            dog=dog,
            reminder_type=reminder_type,
            name=name,
            frequency=frequency,
            reminder_time=time,
            start_date=start_date
        )
        messages.success(request, f"Reminder for {name} added!")
        
    return redirect('medicinereminder')

@login_required
def toggle_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, dog__owner=request.user)
    reminder.is_active = not reminder.is_active
    reminder.save()
    return JsonResponse({'success': True, 'is_active': reminder.is_active})

@login_required
def vet_appointment_view(request):
    if request.method == "POST":
        dog_id = request.POST.get('dog')
        vet_id = request.POST.get('vet')
        service_type = request.POST.get('service_type')
        date_str = request.POST.get('date')
        time = request.POST.get('time')
        notes = request.POST.get('notes', '')

        # Past date check
        from django.utils import timezone
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if booking_date < timezone.now().date():
            messages.error(request, "You cannot book appointments in the past.")
            return redirect('vetappointment')

        dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
        vet = get_object_or_404(Veterinarian, id=vet_id)

        # Duplicate check
        if Appointment.objects.filter(dog=dog, veterinarian=vet, appointment_date=booking_date, appointment_time=time, status__in=['Confirmed', 'Pending']).exists():
            messages.error(request, f"There is already a booking for {dog.name} with this vet at this exact time.")
            return redirect('vetappointment')

        appointment = Appointment.objects.create(
            user=request.user,
            dog=dog,
            veterinarian=vet,
            service_type=service_type,
            appointment_date=booking_date,
            appointment_time=time,
            notes=notes,
            status='Pending',
            amount=vet.consultation_fee
        )
        messages.success(request, f"Appointment initialized. Please complete the payment to confirm it.")
        return redirect('vet_checkout', appointment_id=appointment.id)

    # GET request logic
    # Fetch only upcoming confirmed and pending appointments
    from django.utils import timezone
    now = timezone.now()
    appointments = Appointment.objects.filter(
        Q(appointment_date__gt=now.date()) | Q(appointment_date=now.date(), appointment_time__gte=now.time()),
        user=request.user, 
        status__in=['Confirmed', 'Pending']
    ).order_by('appointment_date', 'appointment_time')
    
    # Fetch veterinarians sorted by rating
    veterinarians = Veterinarian.objects.exclude(specialty__icontains='Grooming').order_by('-rating')
    
    # Fetch user's dogs
    dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)
    
    # Ensure there are dogs for the user for the demo
    if not dogs.exists():
        # Let's create dummy dog for the demo purpose if requested user exists
        Dog.objects.create(owner=request.user, name="Buddy", breed="Golden Retriever")
        Dog.objects.create(owner=request.user, name="Max", breed="Golden Retriever")
        dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)

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
        date_str = request.POST.get('date')
        time = request.POST.get('time')
        notes = request.POST.get('notes', '')

        # Past date check
        from django.utils import timezone
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if booking_date < timezone.now().date():
            messages.error(request, "You cannot book grooming services in the past.")
            return redirect('groomingbooking')

        dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
        service = get_object_or_404(GroomingService, id=service_id)
        salon = GroomingSalon.objects.first()

        # Duplicate check
        if GroomingBooking.objects.filter(dog=dog, booking_date=booking_date, booking_time=time, status__in=['Confirmed', 'Pending']).exists():
            messages.error(request, f"There is already a grooming booking for {dog.name} at this exact time.")
            return redirect('groomingbooking')

        booking = GroomingBooking.objects.create(
            user=request.user,
            dog=dog,
            service=service,
            salon=salon,
            booking_date=booking_date,
            booking_time=time,
            notes=notes,
            status='Pending',
            amount=service.price
        )
        messages.success(request, "Grooming booking initialized. Please complete the payment to confirm it.")
        return redirect('grooming_checkout', booking_id=booking.id)

    # GET request logic
    from django.utils import timezone
    now = timezone.now()
    bookings = GroomingBooking.objects.filter(
        Q(booking_date__gt=now.date()) | Q(booking_date=now.date(), booking_time__gte=now.time()),
        user=request.user, 
        status__in=['Confirmed', 'Pending']
    ).order_by('booking_date', 'booking_time')
    services = GroomingService.objects.all()
    salon = GroomingSalon.objects.first()
    dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)
    
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
    from django.utils import timezone
    now = timezone.now()
    today = now.date()
    now_time = now.time()
    dogs = Dog.objects.filter(owner=user, is_adoption_post=False)
    appointments = Appointment.objects.filter(
        Q(appointment_date__gt=today) | Q(appointment_date=today, appointment_time__gte=now_time),
        user=user, status='Confirmed'
    ).order_by('appointment_date')[:5]
    grooming_bookings = GroomingBooking.objects.filter(
        Q(booking_date__gt=today) | Q(booking_date=today, booking_time__gte=now_time),
        user=user, status='Confirmed'
    ).order_by('booking_date')[:5]
    
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
    try:
        if request.method == "GET":
            user = request.user
            dogs = Dog.objects.filter(owner=user, is_adoption_post=False)
            
            from shop.models import Order
            from grooming.models import GroomingBooking
            from django.db.models import Sum
            from django.utils import timezone
            
            # Calculate Stats
            from django.utils import timezone
            now = timezone.now()
            today = now.date()
            now_time = now.time()
            appointments_count = Appointment.objects.filter(
                Q(appointment_date__gt=today) | Q(appointment_date=today, appointment_time__gte=now_time),
                user=user, status='Confirmed'
            ).count()
            grooming_count = GroomingBooking.objects.filter(
                Q(booking_date__gt=today) | Q(booking_date=today, booking_time__gte=now_time),
                user=user, status='Confirmed'
            ).count()
            orders_count = Order.objects.filter(user=user, paid=True).count()
            
            # Total Spent
            spent_orders = Order.objects.filter(user=user, paid=True).aggregate(total=Sum('amount'))['total'] or 0
            spent_appts = Appointment.objects.filter(user=user, paid=True).aggregate(total=Sum('amount'))['total'] or 0
            spent_grooming = GroomingBooking.objects.filter(user=user, paid=True).aggregate(total=Sum('amount'))['total'] or 0
            total_spent = spent_orders + spent_appts + spent_grooming
            
            # Update Investment label to Expenses in the stats if it exists
            # This is already handled by template now.
            
            # Upcoming Events
            upcoming_appts = Appointment.objects.filter(
                Q(appointment_date__gt=today) | Q(appointment_date=today, appointment_time__gte=now_time),
                user=user, 
                status__in=['Confirmed', 'Pending']
            ).order_by('appointment_date', 'appointment_time')[:3]
            
            events = []
            for a in upcoming_appts:
                events.append({
                    'title': f"{a.service_type} - {a.dog.name}",
                    'date': a.appointment_date.strftime('%b %d, %Y'),
                    'urgent': a.appointment_date == timezone.now().date()
                })

            # Recent Activity
            activities = []
            # Recent orders
            recent_orders = Order.objects.filter(user=user).order_by('-date')[:2]
            for o in recent_orders:
                activities.append({
                    'action': f"Placed order {o.order_id}",
                    'date': o.date.strftime('%B %d, %Y'),
                    'time': "Recently",
                    'iconClass': 'icon-green',
                    'iconName': 'shopping-bag'
                })
            
            # Recent appts
            recent_appts = Appointment.objects.filter(user=user).order_by('-id')[:2]
            for a in recent_appts:
                activities.append({
                    'action': f"Appointment: {a.service_type} for {a.dog.name}",
                    'date': a.appointment_date.strftime('%B %d, %Y'),
                    'time': "Recently",
                    'iconClass': 'icon-blue',
                    'iconName': 'calendar'
                })

            # Achievements
            achievements = [
                { 
                    'name': 'Caring Parent', 
                    'description': 'Completed 5+ vet sessions', 
                    'iconColor': 'yellow', 
                    'unlocked': appointments_count >= 5,
                    'svgPath': '<path d="M7.21 15 2.66 7.14a2 2 0 0 1 .13-2.2L4.4 2.8A2 2 0 0 1 6 2h12a2 2 0 0 1 1.6.8l1.6 2.14a2 2 0 0 1 .14 2.2L16.79 15"/><path d="M11 12 5.12 2.2"/><path d="m13 12 5.88-9.8"/><path d="M8 7h8"/><circle cx="12" cy="17" r="5"/><path d="M12 18v-2h-.5"/>'
                },
                {
                    'name': 'Shopping Star',
                    'description': 'First item purchased',
                    'iconColor': 'blue',
                    'unlocked': orders_count > 0,
                    'svgPath': '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" x2="21" y1="6" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/>'
                },
                {
                    'name': 'Health Champion',
                    'description': 'Added your first dog',
                    'iconColor': 'green',
                    'unlocked': dogs.exists(),
                    'svgPath': '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'
                }
            ]
            
            profile_data = {
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'phone': user.phone or '',
                'location': user.location or '',
                'bio': user.bio or '',
                'joinedDate': user.date_joined.strftime('%B %d, %Y') if user.date_joined else 'N/A',
                'profilePicture': user.profile_picture.url if user.profile_picture else None,
                'coverPicture': user.cover_picture.url if user.cover_picture else None,
                'totalSpent': f"NPR {total_spent:,}",
                'dogs': [
                    {
                        'id': dog.id,
                        'name': dog.name,
                        'breed': dog.breed or 'Unknown',
                        'age': dog.age or 'N/A',
                        'weight': dog.weight or 'N/A',
                        'healthScore': 95, # Mock for now
                        'image': dog.image.url if dog.image else 'https://via.placeholder.com/300x300?text=No+Image'
                    }
                    for dog in dogs
                ],
                'upcomingEvents': events,
                'recentActivity': activities,
                'achievements': achievements,
                'stats': [
                    { 'label': 'My Dogs', 'value': str(dogs.count()), 'iconClass': 'teal', 'trend': '+0', 'iconName': 'dog' },
                    { 'label': 'Appointments', 'value': str(appointments_count), 'iconClass': 'teal', 'trend': '+2', 'iconName': 'calendar-check-2' },
                    { 'label': 'Orders', 'value': str(orders_count), 'iconClass': 'teal', 'trend': '+3', 'iconName': 'package' },
                    { 'label': 'Bookings', 'value': str(grooming_count), 'iconClass': 'orange', 'trend': '+1', 'iconName': 'scissors' }
                ]
            }
            return JsonResponse(profile_data)
        return JsonResponse({'error': 'Invalid request'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
@csrf_exempt
def update_user_profile_api(request):
    """API endpoint to update user profile"""
    if request.method == "POST":
        try:
            # Handle both JSON and Multipart data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            user = request.user
            
            # Update user fields
            if 'first_name' in data:
                user.first_name = data.get('first_name', user.first_name)
            elif 'name' in data:
                # Split full name
                full_name = data.get('name', '').split(' ')
                user.first_name = full_name[0]
                user.last_name = ' '.join(full_name[1:]) if len(full_name) > 1 else ''
            
            if 'last_name' in data:
                user.last_name = data.get('last_name', user.last_name)
            if 'email' in data and data.get('email'):
                new_email = data.get('email').strip()
                from accounts.models import User as UserModel
                if new_email != user.email and UserModel.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                    return JsonResponse({'success': False, 'error': 'This email is already in use.'}, status=400)
                user.email = new_email
            if 'username' in data and data.get('username'):
                new_username = data.get('username').strip()
                from accounts.models import User as UserModel
                if new_username != user.username and UserModel.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                    return JsonResponse({'success': False, 'error': 'This username is already taken.'}, status=400)
                user.username = new_username
            if 'phone' in data:
                user.phone = data.get('phone', user.phone)
            if 'location' in data:
                user.location = data.get('location', user.location)
            if 'bio' in data:
                user.bio = data.get('bio', user.bio)
            # Handle password change
            if 'new_password' in data and data.get('new_password'):
                if not user.check_password(data.get('current_password', '')):
                    return JsonResponse({'success': False, 'error': 'Current password is incorrect.'}, status=400)
                user.set_password(data.get('new_password'))
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
            # Handle Image Uploads
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
            if 'cover_picture' in request.FILES:
                user.cover_picture = request.FILES['cover_picture']

            user.save()
            
            return JsonResponse({
                'success': True,
                'user': {
                    'name': user.get_full_name(),
                    'phone': user.phone,
                    'location': user.location,
                    'bio': user.bio,
                    'profile_picture': user.profile_picture.url if user.profile_picture else None,
                    'cover_picture': user.cover_picture.url if user.cover_picture else None,
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

@login_required
def vet_checkout_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    if appointment.status != 'Pending':
        messages.warning(request, "This appointment is already processed.")
        return redirect('vetappointment')
    
    return render(request, "vet_checkout.html", {'appointment': appointment})

@login_required
def khalti_init_appointment_payment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    # Amount in Paisa
    amount_paisa = int(appointment.amount * 100)
    
    # Return URL: Need to pass some unique ID to verify later
    return_url = request.build_absolute_uri(reverse('khalti_callback'))
    website_url = request.build_absolute_uri('/')
    
    customer_info = {
        "name": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "phone": request.user.phone or "9800000000"
    }
    
    from payment.khalti_utils import initiate_khalti_payment
    response = initiate_khalti_payment(
        amount=amount_paisa,
        purchase_order_id=f"APPT-{appointment.id}",
        purchase_order_name=f"{appointment.service_type} Appointment",
        return_url=return_url,
        website_url=website_url,
        customer_info=customer_info
    )
    
    if "payment_url" in response:
        # Store pidx in the appointment
        appointment.pidx = response['pidx']
        appointment.save()
        return redirect(response['payment_url'])
    else:
        messages.error(request, f"Failed to initiate Khalti payment: {response.get('detail', 'Unknown error')}")
        return redirect('vet_checkout', appointment_id=appointment.id)

@login_required
def khalti_callback_view(request):
    pidx = request.GET.get('pidx') or request.GET.get('transaction_id')
    status = request.GET.get('status')
    purchase_order_id = request.GET.get('purchase_order_id')
    
    if not pidx:
        messages.error(request, "Invalid payment callback.")
        return redirect('vetappointment')

    # Verify payment status using lookup API
    from payment.khalti_utils import verify_khalti_payment
    verification = verify_khalti_payment(pidx)
    
    if verification.get('status') == 'Completed':
        try:
            # 1. Try for Appointment
            if purchase_order_id and purchase_order_id.startswith('APPT-'):
                appt_id = purchase_order_id.split('-')[1]
                appointment = Appointment.objects.get(id=appt_id)
                appointment.paid = True
                appointment.status = 'Confirmed'
                appointment.save()
                send_appointment_email(appointment)
                messages.success(request, "Payment successful! Your appointment is confirmed.")
                return render(request, "payment_success.html", {
                    "message": "Your appointment has been confirmed! 🐾",
                    "redirect_url": "vetappointment",
                    "button_text": "View Appointment"
                })
            
            # 2. Try for Grooming
            elif purchase_order_id and purchase_order_id.startswith('GRM-'):
                booking_id = purchase_order_id.split('-')[1]
                booking = GroomingBooking.objects.get(id=booking_id)
                booking.paid = True
                booking.status = 'Confirmed'
                booking.save()
                send_grooming_email(booking)
                messages.success(request, "Payment successful! Your grooming booking is confirmed.")
                return render(request, "payment_success.html", {
                    "message": "Your grooming session is scheduled! 🐾",
                    "redirect_url": "groomingbooking",
                    "button_text": "View Grooming"
                })
            
            # 3. Try for Shop Order
            elif purchase_order_id and purchase_order_id.startswith('ORD-'):
                order_id_pk = purchase_order_id.split('-')[1]
                order = Order.objects.get(id=order_id_pk)
                order.paid = True
                order.status = 'Processing'
                order.save()
                
                # Update Product Sales and Stock
                for item in order.items.all():
                    product = item.product
                    product.sales += item.quantity
                    product.stock -= item.quantity
                    product.save()
                
                # Clear Cart
                CartItem.objects.filter(user=order.user).delete()
                send_order_email(order)
                messages.success(request, "Payment successful! Your order is being processed.")
                return render(request, "payment_success.html", {
                    "message": "Your order has been placed successfully! 🐾",
                    "redirect_url": "pet_expenses",
                    "button_text": "View Product"
                })
                
            # Fallback for old style or non-prefixed IDs
            else:
                # Fallback check by pidx for all models
                if Appointment.objects.filter(pidx=pidx).exists():
                    obj = Appointment.objects.get(pidx=pidx)
                    obj.paid = True
                    obj.status = 'Confirmed'
                    obj.save()
                    send_appointment_email(obj)
                elif GroomingBooking.objects.filter(pidx=pidx).exists():
                    obj = GroomingBooking.objects.get(pidx=pidx)
                    obj.paid = True
                    obj.status = 'Confirmed'
                    obj.save()
                    send_grooming_email(obj)
                elif Order.objects.filter(pidx=pidx).exists():
                    obj = Order.objects.get(pidx=pidx)
                    obj.paid = True
                    obj.status = 'Processing'
                    obj.save()
                    send_order_email(obj)
                    for item in obj.items.all():
                        item.product.sales += item.quantity
                        item.product.stock -= item.quantity
                        item.product.save()
                    CartItem.objects.filter(user=obj.user).delete()
                
                messages.success(request, "Payment verified successfully!")
                # Determine redirect based on object
                redirect_url = "dashboard"
                button_text = "Go to Dashboard"
                
                if Appointment.objects.filter(pidx=pidx).exists():
                    redirect_url = "vetappointment"
                    button_text = "View Appointment"
                elif GroomingBooking.objects.filter(pidx=pidx).exists():
                    redirect_url = "groomingbooking"
                    button_text = "View Grooming"
                elif Order.objects.filter(pidx=pidx).exists():
                    redirect_url = "pet_expenses"
                    button_text = "View Product"
                
                return render(request, "payment_success.html", {
                    "message": "Your payment has been processed successfully! 🐾",
                    "redirect_url": redirect_url,
                    "button_text": button_text
                })
                
        except Exception as e:
            messages.error(request, f"Error verifying payment record: {str(e)}")
            return redirect('dashboard')
    else:
        messages.error(request, "Payment failed or was cancelled.")
        return redirect('dashboard')

@login_required
def grooming_checkout_view(request, booking_id):
    booking = get_object_or_404(GroomingBooking, id=booking_id, user=request.user)
    if booking.status != 'Pending':
        messages.warning(request, "This booking is already processed.")
        return redirect('groomingbooking')
    
    return render(request, "grooming_checkout.html", {'booking': booking})

@login_required
def khalti_init_grooming_payment(request, booking_id):
    booking = get_object_or_404(GroomingBooking, id=booking_id, user=request.user)
    
    amount_paisa = int(booking.amount * 100)
    return_url = request.build_absolute_uri(reverse('khalti_callback'))
    website_url = request.build_absolute_uri('/')
    
    customer_info = {
        "name": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "phone": request.user.phone or "9800000000"
    }
    
    from payment.khalti_utils import initiate_khalti_payment
    response = initiate_khalti_payment(
        amount=amount_paisa,
        purchase_order_id=f"GRM-{booking.id}",
        purchase_order_name=f"Grooming: {booking.service.name}",
        return_url=return_url,
        website_url=website_url,
        customer_info=customer_info
    )
    
    if "payment_url" in response:
        booking.pidx = response['pidx']
        booking.save()
        return redirect(response['payment_url'])
    else:
        messages.error(request, f"Failed to initiate Khalti payment: {response.get('detail', 'Unknown error')}")
        return redirect('grooming_checkout', booking_id=booking.id)

@login_required
def pet_expenses_view(request):
    user = request.user
    from shop.models import Order
    from grooming.models import GroomingBooking
    from veterinary.models import Appointment
    from django.db.models import Sum

    # Fetch all paid transactions
    orders = Order.objects.filter(user=user, paid=True).order_by('-date')
    appointments = Appointment.objects.filter(user=user, paid=True).order_by('-appointment_date')
    grooming = GroomingBooking.objects.filter(user=user, paid=True).order_by('-booking_date')

    # Aggregates
    spent_orders = orders.aggregate(total=Sum('amount'))['total'] or 0
    spent_appts = appointments.aggregate(total=Sum('amount'))['total'] or 0
    spent_grooming = grooming.aggregate(total=Sum('amount'))['total'] or 0
    total_spent = spent_orders + spent_appts + spent_grooming

    # Combine into a timeline
    transactions = []
    for o in orders:
        transactions.append({
            'type': 'Shop Order',
            'detail': f"Order {o.order_id}",
            'amount': o.amount,
            'date': o.date,
            'icon': 'shopping-bag',
            'color': 'teal'
        })
    for a in appointments:
        transactions.append({
            'type': 'Veterinary',
            'detail': f"{a.service_type} for {a.dog.name}",
            'amount': a.amount,
            'date': a.appointment_date,
            'icon': 'stethoscope',
            'color': 'blue'
        })
    for g in grooming:
        transactions.append({
            'type': 'Grooming',
            'detail': f"{g.service.name if g.service else 'Service'} for {g.dog.name}",
            'amount': g.amount,
            'date': g.booking_date,
            'icon': 'scissors',
            'color': 'orange'
        })

    # Sort by date
    # Harmonize date types (some are date, some are datetime)
    from datetime import datetime, date
    def get_date(val):
        if isinstance(val, datetime):
            return val.date()
        return val

    transactions.sort(key=lambda x: get_date(x['date']), reverse=True)

    context = {
        'total_spent': total_spent,
        'spent_orders': spent_orders,
        'spent_appts': spent_appts,
        'spent_grooming': spent_grooming,
        'transactions': transactions,
    }
    return render(request, 'pet_expenses.html', context)

