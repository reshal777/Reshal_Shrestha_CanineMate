import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import User
from shop.models import Product, Order, OrderItem, ProductReview
from pets.models import Dog, AdoptionRequest, HealthRecord, Vaccination, Medication
from grooming.models import GroomingBooking
from veterinary.models import Appointment
from home.models import ContactMessage
from home.email_utils import send_order_email, send_appointment_email, send_grooming_email, send_adoption_approval_email_to_poster
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.paginator import Paginator

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

def apply_time_range_filter(queryset, date_field, request):
    time_range = request.GET.get('time_range')
    if not time_range:
        return queryset
    
    now = timezone.now()
    if time_range == '1w':
        start_date = now - timedelta(days=7)
    elif time_range == '1m':
        start_date = now - timedelta(days=30)
    elif time_range == '1y':
        start_date = now - timedelta(days=365)
    else:
        return queryset

    try:
        model = queryset.model
        field = model._meta.get_field(date_field.split('__')[0])
        from django.db.models import DateField as DjDateField, DateTimeField as DjDateTimeField
        if isinstance(field, DjDateField) and not isinstance(field, DjDateTimeField):
            return queryset.filter(**{f"{date_field}__gte": start_date.date()})
    except Exception:
        pass
        
    return queryset.filter(**{f"{date_field}__gte": start_date})

def admin_login_view(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if not user:
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

@admin_required
def admin_dashboard_view(request):
    products_qs = apply_time_range_filter(Product.objects.all(), 'created_at', request)
    users_qs = apply_time_range_filter(User.objects.filter(is_superuser=False, is_staff=False), 'date_joined', request)
    orders_qs = apply_time_range_filter(Order.objects.all(), 'date', request)
    adoption_reqs_qs = apply_time_range_filter(AdoptionRequest.objects.all(), 'created_at', request)
    
    product_count = products_qs.count()
    user_count = users_qs.count()
    order_count = orders_qs.count()
    adoption_request_count = adoption_reqs_qs.filter(status='Pending').count()
    
    order_rev_qs = apply_time_range_filter(Order.objects.filter(paid=True), 'date', request)
    vet_rev_qs = apply_time_range_filter(Appointment.objects.filter(paid=True), 'appointment_date', request)
    grooming_rev_qs = apply_time_range_filter(GroomingBooking.objects.filter(paid=True), 'booking_date', request)

    order_revenue = order_rev_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    vet_revenue = vet_rev_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    grooming_revenue = grooming_rev_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    total_revenue = order_revenue + vet_revenue + grooming_revenue
    
    order_pct = (order_revenue / total_revenue * 100) if total_revenue > 0 else 0
    vet_pct = (vet_revenue / total_revenue * 100) if total_revenue > 0 else 0
    grooming_pct = (grooming_revenue / total_revenue * 100) if total_revenue > 0 else 0
 
    recent_users = users_qs.annotate(
        dog_count=Count('dogs', filter=Q(dogs__is_adoption_post=False), distinct=True)
    ).order_by('-date_joined')[:5]
    
    top_products = products_qs.order_by('-sales')[:5]
    top_products_list = []
    for p in top_products:
        top_products_list.append({
            'name': p.name,
            'sales': p.sales,
            'price': float(p.price),
            'revenue': float(p.price) * p.sales,
            'trend': 'up' if p.sales > 0 else 'down'
        })
    
    orders_recent = order_rev_qs.order_by('-date')[:5]
    vet_recent = vet_rev_qs.order_by('-appointment_date')[:5]
    groom_recent = grooming_rev_qs.order_by('-booking_date')[:5]
    
    recent_payments = []
    for o in orders_recent:
        recent_payments.append({
            'user': o.user.username, 
            'profile_picture': o.user.profile_picture.url if o.user.profile_picture else None,
            'type': 'Order', 
            'amount': float(o.amount), 
            'method': o.payment_method, 
            'date': o.date.strftime('%Y-%m-%d'), 
            'time': o.date.strftime('%H:%M:%S'), 
            'sort_dt': o.date, 
            'status': 'Success'
        })
    for v in vet_recent:
        dt = timezone.make_aware(datetime.combine(v.appointment_date, v.appointment_time))
        recent_payments.append({
            'user': v.user.username, 
            'profile_picture': v.user.profile_picture.url if v.user.profile_picture else None,
            'type': 'Vet Appointment', 
            'amount': float(v.amount), 
            'method': 'Khalti', 
            'date': v.appointment_date.strftime('%Y-%m-%d'), 
            'time': v.appointment_time.strftime('%H:%M:%S'), 
            'sort_dt': dt, 
            'status': 'Success'
        })
    for g in groom_recent:
        dt = timezone.make_aware(datetime.combine(g.booking_date, g.booking_time))
        recent_payments.append({
            'user': g.user.username, 
            'profile_picture': g.user.profile_picture.url if g.user.profile_picture else None,
            'type': 'Grooming', 
            'amount': float(g.amount), 
            'method': 'Khalti', 
            'date': g.booking_date.strftime('%Y-%m-%d'), 
            'time': g.booking_time.strftime('%H:%M:%S'), 
            'sort_dt': dt, 
            'status': 'Success'
        })

    recent_payments.sort(key=lambda x: x['sort_dt'], reverse=True)
    recent_payments = recent_payments[:5]
    
    recent_users_list = []
    for u in recent_users:
        recent_users_list.append({
            'name': f"{u.first_name} {u.last_name}" if u.first_name else u.username,
            'profile_picture': u.profile_picture.url if u.profile_picture else None,
            'email': u.email,
            'dogs': u.dog_count,
            'joined': u.date_joined.strftime('%b %d, %Y')
        })
        
    today = timezone.now().date()
    chart_labels = []
    revenue_trend_data = []
    signup_trend_data = []
    
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        day_order_rev = Order.objects.filter(paid=True, date__date=d).aggregate(Sum('amount'))['amount__sum'] or 0
        day_vet_rev = Appointment.objects.filter(paid=True, appointment_date=d).aggregate(Sum('amount'))['amount__sum'] or 0
        day_groom_rev = GroomingBooking.objects.filter(paid=True, booking_date=d).aggregate(Sum('amount'))['amount__sum'] or 0
        revenue_trend_data.append(float(day_order_rev + day_vet_rev + day_groom_rev))
        day_signups = User.objects.filter(date_joined__date=d).count()
        signup_trend_data.append(day_signups)

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
        'recent_payments_json': json.dumps(recent_payments, default=str),
        'chart_labels_json': json.dumps(chart_labels),
        'revenue_trend_json': json.dumps(revenue_trend_data),
        'signup_trend_json': json.dumps(signup_trend_data),
    })

@admin_required
def admin_reports_view(request):
    order_revenue_total = apply_time_range_filter(Order.objects.filter(paid=True), 'date', request).aggregate(Sum('amount'))['amount__sum'] or 0
    vet_revenue_total = apply_time_range_filter(Appointment.objects.filter(paid=True), 'appointment_date', request).aggregate(Sum('amount'))['amount__sum'] or 0
    grooming_revenue_total = apply_time_range_filter(GroomingBooking.objects.filter(paid=True), 'booking_date', request).aggregate(Sum('amount'))['amount__sum'] or 0
    total_net_revenue = order_revenue_total + vet_revenue_total + grooming_revenue_total

    product_count = apply_time_range_filter(Product.objects.all(), 'created_at', request).count()
    user_count = apply_time_range_filter(User.objects.all(), 'date_joined', request).count()
    order_count = apply_time_range_filter(Order.objects.all(), 'date', request).count()

    summary_stats = [
      { 'label': 'Total Revenue', 'value': f'NPR {total_net_revenue:,.0f}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#22c55e,#16a34a)', 'icon': 'indian-rupee' },
      { 'label': 'Total Users', 'value': f'{user_count}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#4FBDBA,#3da5a2)', 'icon': 'users' },
      { 'label': 'Store Orders', 'value': f'{order_count}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#F4A261,#e89451)', 'icon': 'shopping-bag' },
      { 'label': 'Total Products', 'value': f'{product_count}', 'change': '+0%', 'trend': 'up', 'bg': 'linear-gradient(135deg,#3b82f6,#2563eb)', 'icon': 'package' }
    ]

    from django.db.models.functions import Coalesce
    from django.db.models import FloatField
    customers = User.objects.filter(is_staff=False, is_superuser=False).annotate(
        product_spent=Coalesce(Sum('product_orders__amount', filter=Q(product_orders__paid=True)), 0.0, output_field=FloatField()),
        vet_spent=Coalesce(Sum('appointments__amount', filter=Q(appointments__paid=True)), 0.0, output_field=FloatField()),
        grooming_spent=Coalesce(Sum('grooming_bookings__amount', filter=Q(grooming_bookings__paid=True)), 0.0, output_field=FloatField()),
        order_count=Count('product_orders', filter=Q(product_orders__paid=True), distinct=True)
    )

    top_customers_list = []
    for c in customers:
        total_spent = float(c.product_spent + c.vet_spent + c.grooming_spent)
        if total_spent > 0:
            top_customers_list.append({
                'name': f"{c.first_name} {c.last_name}" if c.first_name else c.username,
                'profile_picture': c.profile_picture.url if c.profile_picture else None,
                'email': c.email,
                'orders': c.order_count,
                'spent': total_spent
            })
    
    # Sort by spent descending and take top 5
    top_customers_list.sort(key=lambda x: x['spent'], reverse=True)
    top_customers_list = top_customers_list[:5]

    today = timezone.now().date()
    monthly_revenue = []
    for i in range(5, -1, -1):
        first_day = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        next_month_first_day = (first_day + timedelta(days=32)).replace(day=1)
        month_label = first_day.strftime('%b')
        ord_rev = Order.objects.filter(paid=True, date__date__gte=first_day, date__date__lt=next_month_first_day).aggregate(Sum('amount'))['amount__sum'] or 0
        vt_rev = Appointment.objects.filter(paid=True, appointment_date__gte=first_day, appointment_date__lt=next_month_first_day).aggregate(Sum('amount'))['amount__sum'] or 0
        gr_rev = GroomingBooking.objects.filter(paid=True, booking_date__gte=first_day, booking_date__lt=next_month_first_day).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_revenue.append({
            'month': month_label,
            'revenue': float(ord_rev + vt_rev + gr_rev),
            'orders': Order.objects.filter(paid=True, date__date__gte=first_day, date__date__lt=next_month_first_day).count()
        })

    category_sales = [
        {'category': 'Shop Products', 'revenue': float(order_revenue_total), 'orders': Order.objects.filter(paid=True).count(), 'percentage': round(order_revenue_total/total_net_revenue*100, 1) if total_net_revenue > 0 else 0},
        {'category': 'Vet Services', 'revenue': float(vet_revenue_total), 'orders': Appointment.objects.filter(status='Completed').count(), 'percentage': round(vet_revenue_total/total_net_revenue*100, 1) if total_net_revenue > 0 else 0},
        {'category': 'Grooming', 'revenue': float(grooming_revenue_total), 'orders': GroomingBooking.objects.filter(status='Completed').count(), 'percentage': round(grooming_revenue_total/total_net_revenue*100, 1) if total_net_revenue > 0 else 0},
    ]

    return render(request, 'admin_app/adminreports.html', {
        'summary_stats_json': json.dumps(summary_stats),
        'top_customers_json': json.dumps(top_customers_list),
        'monthly_revenue_json': json.dumps(monthly_revenue),
        'category_sales_json': json.dumps(category_sales),
        'total_revenue': total_net_revenue
    })

@admin_required
def admin_users_view(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-date_joined')
    users_list = User.objects.filter(is_staff=False, is_superuser=False).annotate(dog_count=Count('dogs', filter=Q(dogs__is_adoption_post=False), distinct=True))
    users_list = apply_time_range_filter(users_list, 'date_joined', request)
    if search_query:
        users_list = users_list.filter(Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query) | Q(email__icontains=search_query) | Q(username__icontains=search_query))
    if status_filter == 'active':
        users_list = users_list.filter(is_active=True)
    elif status_filter == 'inactive':
        users_list = users_list.filter(is_active=False)
    users_list = users_list.order_by(sort_by)
    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    users_stats_qs = User.objects.filter(is_staff=False, is_superuser=False)
    users_stats_qs = apply_time_range_filter(users_stats_qs, 'date_joined', request)
    active_count = users_stats_qs.filter(is_active=True).count()
    inactive_count = users_stats_qs.filter(is_active=False).count()
    total_dogs = apply_time_range_filter(Dog.objects.filter(is_adoption_post=False), 'created_at', request).count()
    return render(request, 'admin_app/adminusers.html', {
        'users': page_obj, 'search_query': search_query, 'status_filter': status_filter, 'sort_by': sort_by,
        'active_count': active_count, 'inactive_count': inactive_count, 'total_dogs': total_dogs,
    })

@admin_required
def admin_user_edit_view(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.username = request.POST.get('username')
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
        user.delete()
        messages.success(request, f"User {user.username} deleted permanently.")
    return redirect('admin_users')

@admin_required
def admin_products_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Product.objects.create(name=request.POST.get('name'), category=request.POST.get('category'), price=request.POST.get('price'), stock=request.POST.get('stock'), image=request.FILES.get('image'))
            messages.success(request, "Product created successfully.")
        elif action == 'edit':
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.price = request.POST.get('price')
            product.stock = request.POST.get('stock')
            if request.FILES.get('image'): product.image = request.FILES.get('image')
            product.save()
            messages.success(request, "Product updated successfully.")
        elif action == 'delete':
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            product.delete()
            messages.success(request, "Product deleted successfully.")
        return redirect('admin_products')
    products = Product.objects.all().order_by('-id')
    products = apply_time_range_filter(products, 'created_at', request)
    return render(request, 'admin_app/adminproducts.html', {'products': products, 'total_products': products.count(), 'out_of_stock': products.filter(stock=0).count()})

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
    orders_list = Order.objects.all().prefetch_related('items__product', 'product').order_by('-date')
    orders_list = apply_time_range_filter(orders_list, 'date', request)
    total_orders = orders_list.count()
    total_revenue = orders_list.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    paginator = Paginator(orders_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_app/adminorders.html', {'orders': page_obj, 'total_orders': total_orders, 'total_revenue': total_revenue})

@admin_required
def admin_adoption_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['approve', 'reject', 'delete']:
            req_id = request.POST.get('req_id')
            req = get_object_or_404(AdoptionRequest, id=req_id)
            if action == 'approve':
                req.status = 'Approved'
                req.save()
                if req.dog and req.dog.owner: send_adoption_approval_email_to_poster(req)
                messages.success(request, f"Adoption request approved for {req.full_name}.")
            elif action == 'reject':
                req.status = 'Rejected'
                req.save()
                messages.success(request, "Adoption request rejected.")
            elif action == 'delete':
                req.delete()
                messages.success(request, "Adoption request deleted.")
            return redirect('admin_adoption')
        elif action == 'create_listing':
            Dog.objects.create(owner=request.user, name=request.POST.get('name'), breed=request.POST.get('breed'), age=request.POST.get('age'), gender=request.POST.get('gender'), weight=request.POST.get('weight'), color=request.POST.get('color'), description=request.POST.get('description'), location=request.POST.get('location'), is_vaccinated=request.POST.get('is_vaccinated') == 'on', image=request.FILES.get('image'), is_adoptable=True, is_adoption_post=True)
            messages.success(request, "New adoption listing posted successfully.")
            return redirect('admin_adoption')
        elif action == 'edit_listing':
            dog = get_object_or_404(Dog, id=request.POST.get('dog_id'))
            dog.name = request.POST.get('name'); dog.breed = request.POST.get('breed'); dog.age = request.POST.get('age'); dog.gender = request.POST.get('gender'); dog.weight = request.POST.get('weight'); dog.color = request.POST.get('color'); dog.description = request.POST.get('description'); dog.location = request.POST.get('location'); dog.is_vaccinated = request.POST.get('is_vaccinated') == 'on';
            if request.FILES.get('image'): dog.image = request.FILES.get('image')
            dog.save()
            messages.success(request, f"Listing for {dog.name} updated.")
            return redirect('admin_adoption')
        elif action == 'delete_listing':
            get_object_or_404(Dog, id=request.POST.get('dog_id')).delete()
            messages.success(request, "Adoption listing deleted.")
            return redirect('admin_adoption')
    requests_qs = apply_time_range_filter(AdoptionRequest.objects.all(), 'created_at', request).order_by('-created_at')
    listings_qs = apply_time_range_filter(Dog.objects.filter(is_adoptable=True), 'created_at', request).order_by('-id')
    req_paginator = Paginator(requests_qs, 6); req_page = request.GET.get('req_page'); requests_obj = req_paginator.get_page(req_page)
    list_paginator = Paginator(listings_qs, 6); list_page = request.GET.get('list_page'); listings_obj = list_paginator.get_page(list_page)
    return render(request, 'admin_app/adminadoption.html', {'requests': requests_obj, 'listings': listings_obj, 'total_listings': listings_qs.count(), 'booked_count': listings_qs.filter(adoption_requests__status='Approved').distinct().count(), 'pending_count': requests_qs.filter(status='Pending').count(), 'active_tab': request.GET.get('tab', 'requests')})

@admin_required
def admin_grooming_view(request):
    from grooming.models import GroomingService
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_price':
            service = get_object_or_404(GroomingService, id=request.POST.get('service_id'))
            service.price = request.POST.get('price'); service.save()
            messages.success(request, f"Price updated for {service.name}!")
        else:
            booking = get_object_or_404(GroomingBooking, id=request.POST.get('booking_id'))
            if action == 'confirm': booking.status = 'Confirmed'
            elif action == 'complete': booking.status = 'Completed'
            elif action == 'delete': booking.delete(); messages.success(request, "Booking deleted."); return redirect('admin_grooming')
            booking.save(); messages.success(request, f"Booking {action}ed!")
        return redirect('admin_grooming')
    bookings_qs = apply_time_range_filter(GroomingBooking.objects.all(), 'booking_date', request).order_by('-booking_date')
    page_obj = Paginator(bookings_qs, 10).get_page(request.GET.get('page'))
    return render(request, 'admin_app/admingrooming.html', {'bookings': page_obj, 'services': GroomingService.objects.all(), 'total_bookings': bookings_qs.count(), 'pending': bookings_qs.filter(status='Pending').count()})

@admin_required
def admin_health_view(request):
    if request.method == 'POST':
        action = request.POST.get('action'); record_id = request.POST.get('record_id'); model_name = request.POST.get('model', 'HealthRecord')
        if action == 'delete':
            if model_name == 'HealthRecord': get_object_or_404(HealthRecord, id=record_id).delete()
            elif model_name == 'Vaccination': get_object_or_404(Vaccination, id=record_id).delete()
            elif model_name == 'Medication': get_object_or_404(Medication, id=record_id).delete()
            messages.success(request, "Record deleted.")
        return redirect('admin_health')
    all_health_data = []
    for r in apply_time_range_filter(HealthRecord.objects.all(), 'date', request): all_health_data.append({'dog': r.dog, 'record_type': r.record_type, 'date': r.date, 'notes': r.notes, 'id': r.id, 'model': 'HealthRecord'})
    for v in apply_time_range_filter(Vaccination.objects.all(), 'date_administered', request): all_health_data.append({'dog': v.dog, 'record_type': f"Vaccination: {v.name}", 'date': v.date_administered, 'notes': f"Status: {v.status}", 'id': v.id, 'model': 'Vaccination'})
    for m in apply_time_range_filter(Medication.objects.all(), 'last_given', request): all_health_data.append({'dog': m.dog, 'record_type': f"Medication: {m.name}", 'date': m.last_given, 'notes': f"Freq: {m.frequency}", 'id': m.id, 'model': 'Medication'})
    all_health_data.sort(key=lambda x: x['date'], reverse=True)
    return render(request, 'admin_app/adminhealth.html', {'records': all_health_data, 'total_records': len(all_health_data)})

@admin_required
def admin_payments_view(request):
    orders = apply_time_range_filter(Order.objects.filter(paid=True), 'date', request)
    appts = apply_time_range_filter(Appointment.objects.filter(paid=True), 'appointment_date', request)
    grooming = apply_time_range_filter(GroomingBooking.objects.filter(paid=True), 'booking_date', request)
    payments = []
    for o in orders: payments.append({'user': o.user, 'type': 'Order', 'amount': o.amount, 'date': o.date, 'method': o.payment_method, 'status': 'Success'})
    for v in appts: payments.append({'user': v.user, 'type': 'Vet Appointment', 'amount': v.amount, 'date': timezone.make_aware(datetime.combine(v.appointment_date, v.appointment_time)), 'method': 'Khalti', 'status': 'Success'})
    for g in grooming: payments.append({'user': g.user, 'type': 'Grooming', 'amount': g.amount, 'date': timezone.make_aware(datetime.combine(g.booking_date, g.booking_time)), 'method': 'Khalti', 'status': 'Success'})
    payments.sort(key=lambda x: x['date'], reverse=True)
    return render(request, 'admin_app/adminpayments.html', {'payments': payments, 'total_revenue': sum(p['amount'] for p in payments)})

@admin_required
def admin_pets_view(request):
    if request.method == 'POST':
        action = request.POST.get('action'); pet = get_object_or_404(Dog, id=request.POST.get('pet_id'))
        if action == 'delete': pet.delete(); messages.success(request, "Pet deleted.")
        elif action == 'edit': pet.name = request.POST.get('name'); pet.breed = request.POST.get('breed'); pet.age = request.POST.get('age'); pet.gender = request.POST.get('gender'); pet.location = request.POST.get('location'); pet.is_vaccinated = request.POST.get('is_vaccinated') == 'on';
        if request.FILES.get('image'): pet.image = request.FILES.get('image')
        pet.save(); messages.success(request, "Pet updated.")
        return redirect('admin_pets')
    search_query = request.GET.get('search', ''); breed_filter = request.GET.get('breed', 'all')
    pets = Dog.objects.filter(owner__is_staff=False, is_adoption_post=False)
    pets = apply_time_range_filter(pets, 'created_at', request)
    if search_query: pets = pets.filter(Q(name__icontains=search_query) | Q(breed__icontains=search_query) | Q(owner__username__icontains=search_query))
    if breed_filter != 'all': pets = pets.filter(breed=breed_filter)
    page_obj = Paginator(pets.order_by('-id'), 10).get_page(request.GET.get('page'))
    return render(request, 'admin_app/adminpets.html', {'pets': page_obj, 'total_pets': Dog.objects.filter(owner__is_staff=False, is_adoption_post=False).count(), 'healthy_pets': pets.filter(health_records__isnull=True).count(), 'search_query': search_query, 'breed_filter': breed_filter, 'breeds': Dog.objects.values_list('breed', flat=True).distinct().order_by('breed')})

@admin_required
def admin_veterinary_view(request):
    from veterinary.models import Veterinarian
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_price':
            vet = get_object_or_404(Veterinarian, id=request.POST.get('vet_id'))
            vet.consultation_fee = request.POST.get('consultation_fee'); vet.regular_checkup_fee = request.POST.get('regular_checkup_fee'); vet.vaccination_fee = request.POST.get('vaccination_fee'); vet.emergency_fee = request.POST.get('emergency_fee'); vet.followup_fee = request.POST.get('followup_fee'); vet.save(); messages.success(request, "Fees updated!")
        else:
            appt = get_object_or_404(Appointment, id=request.POST.get('appointment_id'))
            if action == 'confirm': appt.status = 'Confirmed'
            elif action == 'complete': appt.status = 'Completed'
            elif action == 'delete': appt.delete(); messages.success(request, "Appointment deleted."); return redirect('admin_veterinary')
            appt.save(); messages.success(request, f"Appointment {action}ed!")
        return redirect('admin_veterinary')
    appts = apply_time_range_filter(Appointment.objects.all(), 'appointment_date', request).order_by('-appointment_date')
    return render(request, 'admin_app/adminvetenary.html', {'appointments': Paginator(appts, 10).get_page(request.GET.get('page')), 'veterinarians': Veterinarian.objects.all(), 'total_appointments': appts.count()})

@admin_required
def admin_reviews_view(request):
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        review = get_object_or_404(ProductReview, id=request.POST.get('review_id')); product = review.product
        review.delete(); reviews = product.reviews.all(); product.reviews_count = reviews.count(); product.rating = sum(r.rating for r in reviews) / product.reviews_count if product.reviews_count > 0 else 0; product.save(); messages.success(request, "Review deleted.")
        return redirect('admin_reviews')
    reviews = apply_time_range_filter(ProductReview.objects.all(), 'created_at', request).order_by('-created_at')
    return render(request, 'admin_app/adminreviews.html', {'reviews': reviews, 'total_reviews': reviews.count(), 'avg_rating': reviews.aggregate(Sum('rating'))['rating__sum'] / reviews.count() if reviews.count() > 0 else 0})

@admin_required
def admin_messages_view(request):
    msgs = apply_time_range_filter(ContactMessage.objects.all(), 'created_at', request).order_by('-created_at')
    if request.method == "POST":
        msg = get_object_or_404(ContactMessage, id=request.POST.get('msg_id')); action = request.POST.get('action')
        if action == 'resolve': msg.is_resolved = not msg.is_resolved; msg.save()
        elif action == 'delete': msg.delete()
        messages.success(request, "Message updated."); return redirect('admin_messages')
    return render(request, "admin_app/adminmessages.html", {'messages_list': msgs})
