from django.urls import path
from . import views

urlpatterns = [
    path('adoption/', views.adoption_listing_view, name='adoption'),
    path('contact/', views.contact_us_view, name='contact'),
    path('shop/', views.shop_view, name='shop'),
    path('cart/', views.cart_view, name='cart'),
    path('product/<int:product_id>/', views.product_details_view, name='product_details'),
    path('checkout/', views.checkout_view, name='checkout'),
]
