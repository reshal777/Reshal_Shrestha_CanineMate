import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import User
from .models import Product, Order

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
            
    return render(request, 'admin_login.html')

@admin_required
def admin_logout_view(request):
    auth_logout(request)
    return redirect('login')

from django.core.paginator import Paginator
from django.db.models import Q, Count

@admin_required
def admin_dashboard_view(request):
    product_count = Product.objects.count()
    user_count = User.objects.count()
    order_count = Order.objects.count()
    
    # Fetch 5 most recent users with their dog counts
    recent_users = User.objects.annotate(dog_count=Count('dogs')).order_by('-date_joined')[:5]
    
    # Fetch 5 most recent orders
    recent_orders = Order.objects.select_related('user').order_by('-date')[:5]
    
    return render(request, 'admindashboard.html', {
        'product_count': product_count,
        'user_count': user_count,
        'order_count': order_count,
        'recent_users': recent_users,
        'recent_orders': recent_orders
    })

@admin_required
def admin_users_view(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-date_joined')
    
    users_list = User.objects.filter(is_staff=False).annotate(dog_count=Count('dogs'))
    
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
    
    return render(request, 'adminusers.html', {
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
                
    return render(request, 'admin_user_form.html', {'title': 'Create User'})

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
            
    return render(request, 'admin_user_form.html', {'user_obj': user, 'title': 'Edit User'})

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
                stock=request.POST.get('stock')
            )
            messages.success(request, "Product created successfully.")
        elif action == 'edit':
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.price = request.POST.get('price')
            product.stock = request.POST.get('stock')
            product.save()
            messages.success(request, "Product updated successfully.")
        elif action == 'delete':
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            product.delete()
            messages.success(request, "Product deleted successfully.")
        return redirect('admin_products')

    products = Product.objects.all().order_by('-id')
    return render(request, 'adminproducts.html', {'products': products})

@admin_required
def admin_orders_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            order = get_object_or_404(Order, id=request.POST.get('order_id'))
            order.status = request.POST.get('status')
            order.save()
            messages.success(request, "Order status updated!")
        return redirect('admin_orders')

    orders = Order.objects.all().order_by('-date')
    return render(request, 'adminorders.html', {'orders': orders})

# Optional: Add API endpoints or handling logic for creating/deleting things via JSON to match your frontend scripts.
