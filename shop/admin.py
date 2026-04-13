from django.contrib import admin
from .models import Product, Order, OrderItem, ProductReview

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'rating', 'sales')
    list_filter = ('category',)
    search_fields = ('name', 'category')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'amount', 'status', 'paid', 'payment_method', 'pidx', 'date')
    list_filter = ('status', 'paid', 'date', 'payment_method')
    search_fields = ('order_id', 'user__username', 'first_name', 'last_name', 'email')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('product',)
