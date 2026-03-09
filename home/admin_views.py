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

@admin_required
def admin_dashboard_view(request):
    product_count = Product.objects.count()
    user_count = User.objects.count()
    order_count = Order.objects.count()
    
    return render(request, 'admindashboard.html', {
        'product_count': product_count,
        'user_count': user_count,
        'order_count': order_count
    })

@admin_required
def admin_users_view(request):
    users = User.objects.all().order_by('-date_joined') if hasattr(User, 'date_joined') else User.objects.all().order_by('-user_id')
    return render(request, 'adminusers.html', {'users': users})

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
