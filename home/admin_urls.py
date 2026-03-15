from django.urls import path
from . import admin_views

urlpatterns = [
    path('login/', admin_views.admin_login_view, name='admin_login'),
    path('logout/', admin_views.admin_logout_view, name='admin_logout'),
    path('dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('users/', admin_views.admin_users_view, name='admin_users'),
    path('users/create/', admin_views.admin_user_create_view, name='admin_user_create'),
    path('users/edit/<int:user_id>/', admin_views.admin_user_edit_view, name='admin_user_edit'),
    path('users/delete/<int:user_id>/', admin_views.admin_user_delete_view, name='admin_user_delete'),
    path('products/', admin_views.admin_products_view, name='admin_products'),
    path('orders/', admin_views.admin_orders_view, name='admin_orders'),
]
