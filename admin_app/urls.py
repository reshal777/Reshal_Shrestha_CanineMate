from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard_view, name='admin_dashboard'),
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
    path('users/', views.admin_users_view, name='admin_users'),
    path('users/create/', views.admin_user_create_view, name='admin_user_create'),
    path('users/edit/<int:user_id>/', views.admin_user_edit_view, name='admin_user_edit'),
    path('users/delete/<int:user_id>/', views.admin_user_delete_view, name='admin_user_delete'),
    path('products/', views.admin_products_view, name='admin_products'),
    path('orders/', views.admin_orders_view, name='admin_orders'),
    
    # New views to map the additional templates
    path('adoption/', views.admin_adoption_view, name='admin_adoption'),
    path('grooming/', views.admin_grooming_view, name='admin_grooming'),
    path('health/', views.admin_health_view, name='admin_health'),
    path('payments/', views.admin_payments_view, name='admin_payments'),
    path('pets/', views.admin_pets_view, name='admin_pets'),
    path('reports/', views.admin_reports_view, name='admin_reports'),
    path('veterinary/', views.admin_veterinary_view, name='admin_veterinary'),
]
