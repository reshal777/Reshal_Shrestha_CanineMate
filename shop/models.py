from django.db import models
from django.conf import settings

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Food')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percent = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    sales = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'home_product'

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    order_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    paid = models.BooleanField(default=False)
    pidx = models.CharField(max_length=100, blank=True, null=True)
    
    # Billing/Shipping Info
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'home_order'

    def save(self, *args, **kwargs):
        if not self.order_id:
            import uuid
            self.order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    @property
    def get_categories(self):
        if self.product:
            return self.product.category
        cats = self.items.values_list('product__category', flat=True).distinct()
        return ", ".join(list(cats))

    @property
    def get_product_names(self):
        if self.product:
            return self.product.name
        names = self.items.values_list('product__name', flat=True)
        return ", ".join(list(names))

    def __str__(self):
        return f"{self.order_id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'home_orderitem'

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order: {self.order.order_id})"

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'home_cartitem'
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.user.username}'s cart"

    @property
    def total_price(self):
        return self.product.price * self.quantity
