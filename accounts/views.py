from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import User 
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin:index")
        return redirect("dashboard")
        
    if request.method == "POST":
        login_input = request.POST.get("email", "").strip() # This field will now handle both email and username
        password = request.POST.get("password", "")

        if not login_input or not password:
            messages.error(request, "Email/Username and password are required.")
            return redirect("login")

        # Try to authenticate with username first (since admin uses 'admin' username)
        user = authenticate(request, username=login_input, password=password)
        
        # If username fails, try to authenticate with email
        if user is None and '@' in login_input:
            from .models import User
            try:
                user_obj = User.objects.get(email__iexact=login_input)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect admin/staff users to the standard Django admin
                if user.is_staff:
                    return redirect("admin:index")
                else:
                    return redirect("dashboard")
            else:
                messages.error(request, "Your account is inactive.")
        else:
            messages.error(request, "Invalid credentials.")

        return redirect("login")

    return render(request, "login.html")


from pets.models import Dog
from veterinary.models import Appointment
from grooming.models import GroomingBooking
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.views.decorators.cache import never_cache

@login_required
@never_cache
def dashboard_view(request):
    # Prevent admin users from accessing regular dashboard
    if request.user.is_staff:
        return redirect("admin:index")
        
    user_dogs = Dog.objects.filter(owner=request.user, is_adoption_post=False)
    now = timezone.now()
    today = now.date()
    
    now_time = now.time()
    
    upcoming_appointments = Appointment.objects.filter(
        Q(appointment_date__gt=today) | Q(appointment_date=today, appointment_time__gte=now_time),
        user=request.user
    ).order_by('appointment_date', 'appointment_time')
    
    upcoming_groomings = GroomingBooking.objects.filter(
        Q(booking_date__gt=today) | Q(booking_date=today, booking_time__gte=now_time),
        user=request.user
    ).order_by('booking_date', 'booking_time')
    
    context = {
        'dogs': user_dogs,
        'appointments': upcoming_appointments,
        'groomings': upcoming_groomings,
    }
    
    return render(request, "dashboard.html", context)

@login_required
@never_cache
def admin_dashboard_view(request):
    # Only allow admin/staff users to access admin dashboard
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect("dashboard")
    return render(request, "admindashboard.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        phone = request.POST.get("phone", "").strip() or None

        if not username or not email or not password:
            messages.error(request, "Username, email, and password are required.")
            return redirect("signup")

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return redirect("signup")

        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                phone=phone
            )
            messages.success(request, "Registration successful! You can now log in.")
            
            
            return redirect("login") 
        except Exception as e:
            messages.error(request, "Something went wrong. Please try again.")
            return redirect("signup")

    return render(request, "signup.html")


def success_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "success.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")