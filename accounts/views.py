from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import User 
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_dashboard")
        return redirect("dashboard")

    # Clear any stale messages from previous sessions (e.g. admin panel messages)
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True  # marks them all as consumed so they won't render

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
                # Redirect admin/staff users to the new admin dashboard
                if user.is_staff:
                    return redirect("admin_dashboard")
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
        return redirect("admin_dashboard")
        
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


def forgot_password_view(request):
    """Show the forgot password page (for unauthenticated users)."""
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('user_settings')
    from django.shortcuts import render
    return render(request, 'forgot_password.html')


def forgot_password_send_view(request):
    """AJAX: Accept an email, find the user, send a password reset link."""
    if request.method != 'POST':
        from django.http import JsonResponse
        return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

    import json
    from django.http import JsonResponse
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    import logging
    logger = logging.getLogger(__name__)

    try:
        data  = json.loads(request.body)
        email = data.get('email', '').strip().lower()
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    # Always return success to avoid email enumeration
    if not email:
        return JsonResponse({'success': True})

    try:
        from accounts.models import User
        user = User.objects.get(email__iexact=email)

        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = request.build_absolute_uri(
            f'/accounts/password-reset/confirm/{uid}/{token}/'
        )

        subject = 'Reset Your CanineMate Password'
        plain_message = (
            f'Hi {user.username},\n\n'
            f'Reset your password here: {reset_url}\n\n'
            f'This link expires in 24 hours.'
        )
        html_message = (
            '<html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;">'
            '<div style="background:linear-gradient(135deg,#4FBDBA,#3da5a2);padding:30px;text-align:center;border-radius:12px 12px 0 0;">'
            '<h1 style="color:#fff;margin:0;font-size:24px;">CanineMate</h1>'
            '<p style="color:rgba(255,255,255,.85);margin:8px 0 0;">Password Reset Request</p>'
            '</div>'
            '<div style="background:#fff;padding:32px;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,.08);">'
            + f'<p>Hi <strong>{user.get_full_name() or user.username}</strong>,</p>'
            '<p>We received a request to reset your CanineMate account password. Click the button below:</p>'
            '<div style="text-align:center;margin:28px 0;">'
            + f'<a href="{reset_url}" style="background:linear-gradient(90deg,#4FBDBA,#3da5a2);color:#fff;text-decoration:none;padding:14px 32px;border-radius:50px;font-weight:600;font-size:16px;display:inline-block;">'
            'Reset My Password</a>'
            '</div>'
            '<p style="font-size:13px;color:#6b7280;">This link will expire in 24 hours. If you did not request a password reset, you can safely ignore this email.</p>'
            '<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">'
            '<p style="font-size:12px;color:#9ca3af;text-align:center;">&copy; 2026 CanineMate</p>'
            '</div>'
            '</body></html>'
        )

        send_mail(
            subject,
            plain_message,
            django_settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Password reset email sent to {email}')
    except Exception as e:
        # Silently fail – don't reveal whether email exists
        logger.warning(f'Password reset request for unknown/failed email {email}: {e}')

    return JsonResponse({'success': True})
