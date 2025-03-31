from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, CartItem, Order, OrderItem, DiscountCode

admin.site.site_header = "PharmaSync Admin"
admin.site.site_title = "PharmaSync Admin Portal"
admin.site.index_title = "Welcome to PharmaSync Admin Portal"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'prescription_type', 'display_image']
    list_filter = ['category', 'prescription_type']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:100px; max-height:100px;" />', obj.image.url)
        return 'No Image'
    display_image.short_description = 'Image'

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'active', 'valid_from', 'valid_to']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity']
    list_filter = ['user', 'product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'subtotal', 'discount_amount', 'total_price', 'payment_method', 'status']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'payment_id']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['product']