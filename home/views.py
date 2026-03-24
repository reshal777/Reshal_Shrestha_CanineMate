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

def index_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
        
    vets = Veterinarian.objects.all()[:4]
    if not vets.exists():
        clinic = Clinic.objects.create(name="CanineMate Pet Centre", location="Kathmandu")
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
            cart_items.delete()
            messages.success(request, "Order placed successfully! We will contact you soon for delivery.")
            return render(request, "payment_success.html", {"message": "Your order has been placed successfully! 🐾"})

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, "checkout.html", context)

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

@login_required
def medicine_reminder_view(request):
    dogs = Dog.objects.filter(owner=request.user)
    reminders = Reminder.objects.filter(dog__owner=request.user).order_by('start_date', 'reminder_time')
    
    # Segmenting for the template
    medicine_reminders = reminders.filter(reminder_type='Medicine')
    vaccine_reminders = reminders.filter(reminder_type='Vaccine')
    
    # Upcoming this week (next 7 days)
    from datetime import date, timedelta
    today = date.today()
    next_week = today + timedelta(days=7)
    upcoming_this_week = reminders.filter(
        is_active=True,
        start_date__gte=today,
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
        date = request.POST.get('date')
        time = request.POST.get('time')
        notes = request.POST.get('notes', '')

        dog = get_object_or_404(Dog, id=dog_id, owner=request.user)
        vet = get_object_or_404(Veterinarian, id=vet_id)

        appointment = Appointment.objects.create(
            user=request.user,
            dog=dog,
            veterinarian=vet,
            service_type=service_type,
            appointment_date=date,
            appointment_time=time,
            notes=notes,
            status='Pending',
            amount=vet.consultation_fee
        )
        messages.success(request, f"Appointment initialized. Please complete the payment to confirm it.")
        return redirect('vet_checkout', appointment_id=appointment.id)

    # GET request logic
    # Fetch confirmed and pending appointments
    appointments = Appointment.objects.filter(
        user=request.user, 
        status__in=['Confirmed', 'Pending']
    ).order_by('appointment_date', 'appointment_time')
    
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

        booking = GroomingBooking.objects.create(
            user=request.user,
            dog=dog,
            service=service,
            salon=salon,
            booking_date=date,
            booking_time=time,
            notes=notes,
            status='Pending',
            amount=service.price
        )
        messages.success(request, "Grooming booking initialized. Please complete the payment to confirm it.")
        return redirect('grooming_checkout', booking_id=booking.id)

    # GET request logic
    bookings = GroomingBooking.objects.filter(
        user=request.user, 
        status__in=['Confirmed', 'Pending']
    ).order_by('booking_date', 'booking_time')
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
        
        from shop.models import Order
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
    
    # Khalti status can be 'Completed' or check for successful verification status code or return values
    if verification.get('status') == 'Completed':
        try:
             appointment = None
             # Try finding by purchase_order_id first
             if purchase_order_id and purchase_order_id.startswith('APPT-'):
                try:
                    appt_id = purchase_order_id.split('-')[1]
                    appointment = Appointment.objects.get(id=appt_id)
                except:
                    pass
             
             # Fallback to pidx if not found
             if not appointment:
                appointment = Appointment.objects.get(pidx=pidx)
             
             appointment.paid = True
             appointment.status = 'Confirmed'
             appointment.save()
             
             messages.success(request, "Payment successful! Your appointment is confirmed.")
             return render(request, "payment_success.html", {"message": "Your appointment has been confirmed! 🐾"})
        except Exception as e:
             # Try for grooming booking
             try:
                 booking = None
                 if purchase_order_id and purchase_order_id.startswith('GRM-'):
                     booking_id = purchase_order_id.split('-')[1]
                     booking = GroomingBooking.objects.get(id=booking_id)
                 else:
                     booking = GroomingBooking.objects.get(pidx=pidx)
                 
                 booking.paid = True
                 booking.status = 'Confirmed'
                 booking.save()
                 
                 messages.success(request, "Payment successful! Your grooming booking is confirmed.")
                 return render(request, "payment_success.html", {"message": "Your grooming session is scheduled! 🐾"})
             except Exception as grooming_e:
                 # Try for shop order
                 try:
                     order = None
                     if purchase_order_id and purchase_order_id.startswith('ORD-'):
                         order_id_pk = purchase_order_id.split('-')[1]
                         order = Order.objects.get(id=order_id_pk)
                     else:
                         order = Order.objects.get(pidx=pidx)
                     
                     order.paid = True
                     order.status = 'Processing'
                     order.save()
                     
                     # Clear Cart
                     CartItem.objects.filter(user=order.user).delete()
                     
                     messages.success(request, "Payment successful! Your order is being processed.")
                     return render(request, "payment_success.html", {"message": "Your order has been placed successfully! 🐾"})
                 except Exception as inner_e:
                     messages.error(request, f"Payment verified but error updating record: {str(inner_e)}")
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
