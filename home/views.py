from django.shortcuts import render

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

def dog_profile_view(request):
    return render(request, "dogprofile.html")

def medicine_reminder_view(request):
    return render(request, "medicinereminder.html")

def vet_appointment_view(request):
    return render(request, "vetappoinment.html")

def grooming_booking_view(request):
    return render(request, "groomingbooking.html")
