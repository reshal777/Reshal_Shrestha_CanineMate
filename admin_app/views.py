import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import User
from shop.models import Product, Order, OrderItem
from pets.models import Dog, AdoptionRequest, HealthRecord, Vaccination, Medication
from grooming.models import GroomingBooking
from veterinary.models import Appointment
from django.db.models import Sum
from datetime import datetime
from django.utils import timezone
def admin_required(view_func):
    """Custom decorator for admin-only views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_login_view(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Since the custom User model uses email as USERNAME_FIELD, authenticate using email.
        # But for demo purposes or convenience, we might check if they used "admin" (which would be their username).
        # We can implement a try-catch for either.
        user = authenticate(request, email=email, password=password)
        if not user:
            # Let's try attempting username fallback if the login form sends a username instead of email
            try:
                user_obj = User.objects.get(username=email)
                user = authenticate(request, email=user_obj.email, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            if user.is_staff or user.is_superuser:
                auth_login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Access denied. Not an admin account.")
        else:
            messages.error(request, "Invalid credentials.")
            
    return render(request, 'admin_app/adminlogin.html')

@admin_required
def admin_logout_view(request):
    auth_logout(request)
    return redirect('login')

from django.core.paginator import Paginator
from django.db.models import Q, Count

@admin_required
def admin_dashboard_view(request):
    product_count = Product.objects.count()
    user_count = User.objects.filter(is_superuser=False, is_staff=False).count()
    order_count = Order.objects.count()
    adoption_request_count = AdoptionRequest.objects.filter(status='Pending').count()
    
    # Calculate Total Revenue
    order_revenue = Order.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    vet_revenue = Appointment.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    grooming_revenue = GroomingBooking.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_revenue = order_revenue + vet_revenue + grooming_revenue
    
    order_pct = (order_revenue / total_revenue * 100) if total_revenue > 0 else 0
    vet_pct = (vet_revenue / total_revenue * 100) if total_revenue > 0 else 0
    grooming_pct = (grooming_revenue / total_revenue * 100) if total_revenue > 0 else 0
 
    # Fetch 5 most recent customers (excluding staff/admins)
    from django.db.models import Q
    recent_users = User.objects.filter(is_superuser=False, is_staff=False).annotate(
        dog_count=Count('dogs', filter=Q(dogs__is_adoption_post=False), distinct=True)
    ).order_by('-date_joined')[:5]
    
    # Fetch top products
    top_products = Product.objects.all().order_by('-sales')[:5]
    top_products_list = []
    for p in top_products:
        top_products_list.append({
            'name': p.name,
            'sales': p.sales,
            'price': float(p.price),
            'revenue': float(p.price) * p.sales,
            'trend': 'up' if p.sales > 0 else 'down'
        })
    
    # Fetch recent payments across all types
    # We will grab orders, appointments, grooming and sort them.
    from itertools import chain
    orders_recent = Order.objects.filter(paid=True).order_by('-date')[:5]
    vet_recent = Appointment.objects.filter(paid=True).order_by('-appointment_date')[:5]
    groom_recent = GroomingBooking.objects.filter(paid=True).order_by('-booking_date')[:5]
    
    recent_payments = []
    for o in orders_recent:
        recent_payments.append({'user': o.user.username, 'type': 'Order', 'amount': float(o.amount), 'method': o.payment_method, 'date': o.date.strftime('%Y-%m-%d'), 'time': o.date.strftime('%H:%M:%S'), 'sort_dt': o.date, 'status': 'Success'})
    for v in vet_recent:
        dt = timezone.make_aware(datetime.combine(v.appointment_date, v.appointment_time))
        recent_payments.append({'user': v.user.username, 'type': 'Vet Appointment', 'amount': float(v.amount), 'method': 'Khalti', 'date': v.appointment_date.strftime('%Y-%m-%d'), 'time': v.appointment_time.strftime('%H:%M:%S'), 'sort_dt': dt, 'status': 'Success'})
    for g in groom_recent:
        dt = timezone.make_aware(datetime.combine(g.booking_date, g.booking_time))
        recent_payments.append({'user': g.user.username, 'type': 'Grooming', 'amount': float(g.amount), 'method': 'Khalti', 'date': g.booking_date.strftime('%Y-%m-%d'), 'time': g.booking_time.strftime('%H:%M:%S'), 'sort_dt': dt, 'status': 'Success'})

    recent_payments.sort(key=lambda x: x['sort_dt'], reverse=True)
    recent_payments = recent_payments[:5]
    
    # Prepare JSON for frontend scripts
    recent_users_list = []
    for u in recent_users:
        recent_users_list.append({
            'name': f"{u.first_name} {u.last_name}" if u.first_name else u.username,
            'email': u.email,
            'dogs': u.dog_count,
            'joined': u.date_joined.strftime('%b %d, %Y')
        })
        
    return render(request, 'admin_app/admindashboard.html', {
        'product_count': product_count,
        'user_count': user_count,
        'order_count': order_count,
        'total_revenue': total_revenue,
        'order_revenue': order_revenue,
        'vet_revenue': vet_revenue,
        'grooming_revenue': grooming_revenue,
        'order_pct': round(order_pct, 1),
        'vet_pct': round(vet_pct, 1),
        'grooming_pct': round(grooming_pct, 1),
        'adoption_request_count': adoption_request_count,
        'recent_users_json': json.dumps(recent_users_list),
        'top_products_json': json.dumps(top_products_list),
        'recent_payments_json': json.dumps(recent_payments, default=str)
    })

@admin_required
def admin_users_view(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-date_joined')
    
    users_list = User.objects.filter(is_staff=False, is_superuser=False).annotate(dog_count=Count('dogs', filter=Q(dogs__is_adoption_post=False), distinct=True))
    
    if search_query:
        users_list = users_list.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
        
    if status_filter == 'active':
        users_list = users_list.filter(is_active=True)
    elif status_filter == 'inactive':
        users_list = users_list.filter(is_active=False)
        
    users_list = users_list.order_by(sort_by)
    
    paginator = Paginator(users_list, 10) # 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    active_count = User.objects.filter(is_staff=False, is_superuser=False, is_active=True).count()
    inactive_count = User.objects.filter(is_staff=False, is_superuser=False, is_active=False).count()
    from pets.models import Dog
    total_dogs = Dog.objects.filter(is_adoption_post=False).count()

    return render(request, 'admin_app/adminusers.html', {
        'users': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'is_active_status': status_filter == 'active',
        'is_inactive_status': status_filter == 'inactive',
        'sort_newest': sort_by == '-date_joined',
        'sort_oldest': sort_by == 'date_joined',
        'sort_username': sort_by == 'username',
        'sort_email': sort_by == 'email',
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_dogs': total_dogs,
    })

@admin_required
def admin_user_create_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            try:
                User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_active=is_active
                )
                messages.success(request, f"User {username} created successfully.")
                return redirect('admin_users')
            except Exception as e:
                messages.error(request, f"Error creating user: {str(e)}")
                
    return render(request, 'admin_app/admin_user_form.html', {'title': 'Create User'})

@admin_required
def admin_user_edit_view(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.username = request.POST.get('username')
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_active = request.POST.get('is_active') == 'on'
        
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)
            
        try:
            user.save()
            messages.success(request, f"User {user.username} updated successfully.")
            return redirect('admin_users')
        except Exception as e:
            messages.error(request, f"Error updating user: {str(e)}")
            
    return render(request, 'admin_app/admin_user_form.html', {'user_obj': user, 'title': 'Edit User'})

@admin_required
def admin_user_delete_view(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f"User {user.username} deactivated.")
        elif action == 'delete':
            user.delete()
            messages.success(request, f"User {user.username} deleted permanently.")
        return redirect('admin_users')
    return redirect('admin_users')


@admin_required
def admin_products_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Product.objects.create(
                name=request.POST.get('name'),
                category=request.POST.get('category'),
                price=request.POST.get('price'),
                stock=request.POST.get('stock'),
                image=request.FILES.get('image')
            )
            messages.success(request, "Product created successfully.")
        elif action == 'edit':
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.price = request.POST.get('price')
            product.stock = request.POST.get('stock')
            if request.FILES.get('image'):
                product.image = request.FILES.get('image')
            product.save()
            messages.success(request, "Product updated successfully.")
        elif action == 'delete':
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            product.delete()
            messages.success(request, "Product deleted successfully.")
        return redirect('admin_products')

    products = Product.objects.all().order_by('-id')
    return render(request, 'admin_app/adminproducts.html', {
        'products': products,
        'total_products': products.count(),
        'out_of_stock': products.filter(stock=0).count()
    })

@admin_required
def admin_orders_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            order = get_object_or_404(Order, id=request.POST.get('order_id'))
            order.status = request.POST.get('status')
            order.save()
            messages.success(request, "Order status updated!")
        elif action == 'delete':
            order = get_object_or_404(Order, id=request.POST.get('order_id'))
            order.delete()
            messages.success(request, "Order deleted permanently.")
        return redirect('admin_orders')

    orders = Order.objects.all().prefetch_related('items__product', 'product').order_by('-date')
    
    from django.db.models import Sum
    total_orders = orders.count()
    total_revenue = orders.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    
    return render(request, 'admin_app/adminorders.html', {
        'orders': orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue
    })

@admin_required
def admin_adoption_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handling Adoption Requests
        if action in ['approve', 'reject', 'delete']:
            req_id = request.POST.get('req_id')
            req = get_object_or_404(AdoptionRequest, id=req_id)
            if action == 'approve':
                req.status = 'Approved'
                req.save()
                # Optionally mark dog as adopted? 
                # req.dog.is_adoptable = False
                # req.dog.save()
                messages.success(request, f"Adoption request approved for {req.full_name}.")
            elif action == 'reject':
                req.status = 'Rejected'
                req.save()
                messages.success(request, "Adoption request rejected.")
            elif action == 'delete':
                req.delete()
                messages.success(request, "Adoption request deleted.")
            return redirect('admin_adoption')

        # Handling Pet Listings (Posting dogs for adoption)
        elif action == 'create_listing':
            Dog.objects.create(
                owner=request.user,
                name=request.POST.get('name'),
                breed=request.POST.get('breed'),
                age=request.POST.get('age'),
                gender=request.POST.get('gender'),
                weight=request.POST.get('weight'),
                color=request.POST.get('color'),
                description=request.POST.get('description'),
                location=request.POST.get('location'),
                is_vaccinated=request.POST.get('is_vaccinated') == 'on',
                image=request.FILES.get('image'),
                is_adoptable=True,
                is_adoption_post=True
            )
            messages.success(request, "New adoption listing posted successfully.")
            return redirect('admin_adoption')
            
        elif action == 'edit_listing':
            dog = get_object_or_404(Dog, id=request.POST.get('dog_id'))
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
            messages.success(request, f"Listing for {dog.name} updated.")
            return redirect('admin_adoption')

        elif action == 'delete_listing':
            dog = get_object_or_404(Dog, id=request.POST.get('dog_id'))
            dog.delete()
            messages.success(request, "Adoption listing deleted.")
            return redirect('admin_adoption')

    requests = AdoptionRequest.objects.all().order_by('-created_at')
    listings = Dog.objects.filter(is_adoptable=True).order_by('-id')
    return render(request, 'admin_app/adminadoption.html', {
        'requests': requests,
        'listings': listings,
        'total_listings': Dog.objects.filter(is_adoptable=True).count(),
        'booked_count': Dog.objects.filter(is_adoptable=True, adoption_requests__status='Approved').distinct().count(),
        'pending_count': requests.filter(status='Pending').count()
    })

@admin_required
def admin_grooming_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        booking_id = request.POST.get('booking_id')
        booking = get_object_or_404(GroomingBooking, id=booking_id)
        if action == 'confirm':
            booking.status = 'Confirmed'
            booking.save()
            messages.success(request, "Grooming booking confirmed!")
        elif action == 'complete':
            booking.status = 'Completed'
            booking.save()
            messages.success(request, "Grooming booking marked as completed!")
        elif action == 'delete':
            booking.delete()
            messages.success(request, "Grooming booking deleted.")
        return redirect('admin_grooming')

    bookings = GroomingBooking.objects.all().order_by('-booking_date')
    
    total_bookings = bookings.count()
    pending = bookings.filter(status='Pending').count()
    
    return render(request, 'admin_app/admingrooming.html', {
        'bookings': bookings,
        'total_bookings': total_bookings,
        'pending': pending
    })

@admin_required
def admin_health_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        record_id = request.POST.get('record_id')
        model_name = request.POST.get('model', 'HealthRecord')
        
        if action == 'delete':
            if model_name == 'HealthRecord':
                record = get_object_or_404(HealthRecord, id=record_id)
                msg = "Health record deleted."
            elif model_name == 'Vaccination':
                record = get_object_or_404(Vaccination, id=record_id)
                msg = "Vaccination record deleted."
            elif model_name == 'Medication':
                record = get_object_or_404(Medication, id=record_id)
                msg = "Medication record deleted."
            else:
                messages.error(request, "Invalid model type.")
                return redirect('admin_health')
                
            record.delete()
            messages.success(request, msg)
        return redirect('admin_health')

    records_query = HealthRecord.objects.all().order_by('-date')
    vaccinations = Vaccination.objects.all().order_by('-date_administered')
    medications = Medication.objects.all().order_by('-last_given')

    all_health_data = []
    for r in records_query:
        all_health_data.append({
            'dog': r.dog,
            'record_type': r.record_type,
            'date': r.date,
            'notes': r.notes,
            'id': r.id,
            'model': 'HealthRecord'
        })
    for v in vaccinations:
        all_health_data.append({
            'dog': v.dog,
            'record_type': f"Vaccination: {v.name}",
            'date': v.date_administered,
            'notes': f"Status: {v.status} | Next Due: {v.next_due_date}",
            'id': v.id,
            'model': 'Vaccination'
        })
    for m in medications:
        all_health_data.append({
            'dog': m.dog,
            'record_type': f"Medication: {m.name}",
            'date': m.last_given,
            'notes': f"Freq: {m.frequency} | Next Due: {m.next_due}",
            'id': m.id,
            'model': 'Medication'
        })

    # Sort by date descending
    all_health_data.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'admin_app/adminhealth.html', {
        'records': all_health_data,
        'total_records': len(all_health_data)
    })

@admin_required
def admin_payments_view(request):
    # Showing all types of transactions
    orders = Order.objects.filter(paid=True).order_by('-date')
    appts = Appointment.objects.filter(paid=True).order_by('-appointment_date')
    grooming = GroomingBooking.objects.filter(paid=True).order_by('-booking_date')
    
    payments = []
    for o in orders:
        payments.append({'user': o.user, 'type': 'Order', 'amount': o.amount, 'date': o.date, 'method': o.payment_method, 'status': 'Success'})
    for v in appts:
        dt = timezone.make_aware(datetime.combine(v.appointment_date, v.appointment_time))
        payments.append({'user': v.user, 'type': 'Vet Appointment', 'amount': v.amount, 'date': dt, 'method': 'Khalti', 'status': 'Success'})
    for g in grooming:
        dt = timezone.make_aware(datetime.combine(g.booking_date, g.booking_time))
        payments.append({'user': g.user, 'type': 'Grooming', 'amount': g.amount, 'date': dt, 'method': 'Khalti', 'status': 'Success'})
        
    payments.sort(key=lambda x: x['date'], reverse=True)
    
    total_revenue = sum(p['amount'] for p in payments)

    return render(request, 'admin_app/adminpayments.html', {
        'payments': payments,
        'total_revenue': total_revenue
    })

@admin_required
def admin_pets_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        pet_id = request.POST.get('pet_id')
        pet = get_object_or_404(Dog, id=pet_id)
        if action == 'delete':
            pet.delete()
            messages.success(request, f"Pet {pet.name} deleted.")
        elif action == 'edit':
            pet.name = request.POST.get('name')
            pet.breed = request.POST.get('breed')
            pet.age = request.POST.get('age')
            pet.gender = request.POST.get('gender')
            pet.location = request.POST.get('location')
            pet.is_vaccinated = request.POST.get('is_vaccinated') == 'on'
            if request.FILES.get('image'):
                pet.image = request.FILES.get('image')
            pet.save()
            messages.success(request, f"Pet {pet.name} updated successfully.")
        return redirect('admin_pets')

    search_query = request.GET.get('search', '')
    breed_filter = request.GET.get('breed', 'all')
    
    pets = Dog.objects.filter(owner__is_staff=False, is_adoption_post=False)
    
    if search_query:
        pets = pets.filter(
            Q(name__icontains=search_query) | 
            Q(breed__icontains=search_query) |
            Q(owner__username__icontains=search_query) |
            Q(owner__email__icontains=search_query)
        )
        
    if breed_filter != 'all':
        pets = pets.filter(breed=breed_filter)
        
    all_pets = Dog.objects.filter(owner__is_staff=False, is_adoption_post=False)
    
    return render(request, 'admin_app/adminpets.html', {
        'pets': pets.order_by('-id'),
        'total_pets': all_pets.count(),
        'healthy_pets': all_pets.filter(health_records__isnull=True).count(), 
        'search_query': search_query,
        'breed_filter': breed_filter,
        'breeds': all_pets.values_list('breed', flat=True).distinct().order_by('breed')
    })

@admin_required
def admin_reports_view(request):
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    import json
    
    # 1. Total Revenue (same logic as dashboard)
    order_revenue_total = Order.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    vet_revenue_total = Appointment.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    grooming_revenue_total = GroomingBooking.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_net_revenue = order_revenue_total + vet_revenue_total + grooming_revenue_total

    # Summary Stats
    product_count = Product.objects.count()
    user_count = User.objects.count()
    order_count = Order.objects.count()

    summary_stats = [
      { 'label': 'Total Revenue', 'value': f'NPR {total_net_revenue:,.0f}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#22c55e,#16a34a)', 'icon': 'indian-rupee' },
      { 'label': 'Total Users', 'value': f'{user_count}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#4FBDBA,#3da5a2)', 'icon': 'users' },
      { 'label': 'Store Orders', 'value': f'{order_count}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#F4A261,#e89451)', 'icon': 'shopping-bag' },
      { 'label': 'Total Products', 'value': f'{product_count}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#3b82f6,#2563eb)', 'icon': 'package' }
    ]

    # 2. Top Customers based on Orders amount only (or we can combine, but order amounts are easier here)
    # Easiest way is to just aggregate spent amounts from Order
    customers = User.objects.annotate(
        total_spent=Sum('product_orders__amount', filter=Q(product_orders__paid=True)),
        order_count=Count('product_orders', filter=Q(product_orders__paid=True))
    ).order_by('-total_spent')[:5]

    top_customers_list = []
    for c in customers:
        if c.total_spent and c.total_spent > 0:
            top_customers_list.append({
                'name': f"{c.first_name} {c.last_name}" if c.first_name else c.username,
                'email': c.email,
                'orders': c.order_count,
                'spent': float(c.total_spent)
            })

    # 3. Monthly Revenue Trend (Last 3 months)
    today = timezone.now().date()
    months = []
    monthly_revenue = []
    for i in range(2, -1, -1):
        # basic approximation of months going backwards
        first_day = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        ord_rev = Order.objects.filter(paid=True, date__date__range=[first_day, last_day]).aggregate(Sum('amount'))['amount__sum'] or 0
        appt_rev = Appointment.objects.filter(paid=True, appointment_date__range=[first_day, last_day]).aggregate(Sum('amount'))['amount__sum'] or 0
        groom_rev = GroomingBooking.objects.filter(paid=True, booking_date__range=[first_day, last_day]).aggregate(Sum('amount'))['amount__sum'] or 0
        m_rev = ord_rev + appt_rev + groom_rev
        
        # approximate orders count
        m_orders = Order.objects.filter(paid=True, date__date__range=[first_day, last_day]).count()

        monthly_revenue.append({
            'month': first_day.strftime('%b'),
            'revenue': float(m_rev),
            'orders': m_orders
        })
        
    # 4. Sales by Category (Real data from OrderItems)
    cats = Product.objects.values_list('category', flat=True).distinct()
    sales_by_category = []
    
    total_rev_all = Order.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    
    for cat in cats:
        if not cat: continue
        # Accurate aggregation from OrderItem
        cat_items = OrderItem.objects.filter(order__paid=True, product__category=cat)
        cat_rev = cat_items.aggregate(total=Sum('price'))['total'] or 0
        cat_qty = cat_items.aggregate(total=Sum('quantity'))['total'] or 0
        
        if cat_rev > 0:
            percentage = round((float(cat_rev) / float(total_rev_all) * 100), 1) if total_rev_all > 0 else 0
            sales_by_category.append({
                'category': cat,
                'revenue': float(cat_rev),
                'orders': int(cat_qty),
                'percentage': percentage
            })
    
    sales_by_category.sort(key=lambda x: x['revenue'], reverse=True)

    return render(request, 'admin_app/adminreports.html', {
        'summary_stats_json': json.dumps(summary_stats),
        'top_customers_json': json.dumps(top_customers_list),
        'monthly_revenue_json': json.dumps(monthly_revenue),
        'category_sales_json': json.dumps(sales_by_category)
    })

@admin_required
def admin_veterinary_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        appt_id = request.POST.get('appointment_id')
        appt = get_object_or_404(Appointment, id=appt_id)
        if action == 'confirm':
            appt.status = 'Confirmed'
            appt.save()
            messages.success(request, "Appointment confirmed!")
        elif action == 'complete':
            appt.status = 'Completed'
            appt.save()
            messages.success(request, "Appointment marked as completed!")
        elif action == 'delete':
            appt.delete()
            messages.success(request, "Appointment deleted.")
        return redirect('admin_veterinary')

    appointments = Appointment.objects.all().order_by('-appointment_date')
    return render(request, 'admin_app/adminvetenary.html', {
        'appointments': appointments,
        'total_appointments': appointments.count()
    })

# Optional: Add API endpoints or handling logic for creating/deleting things via JSON to match your frontend scripts.
