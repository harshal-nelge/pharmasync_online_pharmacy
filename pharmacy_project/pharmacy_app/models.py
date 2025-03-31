from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

class Product(models.Model):
    PRESCRIPTION_CHOICES = [
        ('OTC', 'Over The Counter'),
        ('RX', 'Prescription Required')
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    prescription_type = models.CharField(max_length=3, choices=PRESCRIPTION_CHOICES, default='OTC')
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

class DiscountCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def total_price(self):
        return self.quantity * self.product.price

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]

    PAYMENT_METHOD_CHOICES = [
        ('PAYPAL', 'PayPal'),
        ('RAZORPAY', 'Razorpay')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Added default value
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='PAYPAL')
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        # If this is a new order (no ID yet) and subtotal is not set
        if not self.pk and self.subtotal == 0:
            # Calculate subtotal from order items if they exist
            # Note: This might not work during creation since items might be added after order
            items = self.items.all() if self.pk else []
            if items:
                self.subtotal = sum(item.price * item.quantity for item in items)
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"