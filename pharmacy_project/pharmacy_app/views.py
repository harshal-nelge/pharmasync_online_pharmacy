import paypalrestsdk
import razorpay
import json
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import JsonResponse
from .models import Category, Product, CartItem, Order, OrderItem, DiscountCode
from decimal import Decimal

def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(stock__gt=0)[:8]
    return render(request, 'home.html', {
        'categories': categories,
        'featured_products': featured_products
    })

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(stock__gt=0)
    return render(request, 'products/category_list.html', {
        'category': category,
        'products': products
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'products/product_detail.html', {
        'product': product
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'auth/profile.html', {'orders': orders})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, 
        product=product
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, 'Product added to cart!')
    return redirect('cart')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    
    # Initialize discount variables
    discount_code = None
    discount_amount = Decimal('0.00')
    
    # Process discount code if submitted
    if request.method == 'POST' and 'discount_code' in request.POST:
        code = request.POST.get('discount_code')
        now = datetime.now()
        try:
            discount = DiscountCode.objects.get(
                code=code,
                active=True,
                valid_from__lte=now,
                valid_to__gte=now
            )
            discount_code = discount
            discount_amount = (total * (discount.discount_percent / Decimal('100'))).quantize(Decimal('0.01'))
            messages.success(request, f'Discount code "{code}" applied successfully!')
        except DiscountCode.DoesNotExist:
            messages.error(request, 'Invalid or expired discount code.')
    
    # Calculate grand total with discount
    grand_total = total - discount_amount
    
    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'discount_code': discount_code,
        'discount_amount': discount_amount,
        'grand_total': grand_total
    })

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    
    # Get discount code from session if available
    discount_code_id = request.session.get('discount_code_id')
    discount_code = None
    discount_amount = Decimal('0.00')
    
    if discount_code_id:
        try:
            discount_code = DiscountCode.objects.get(id=discount_code_id)
            total = sum(item.total_price() for item in cart_items)
            discount_amount = (total * (discount_code.discount_percent / Decimal('100'))).quantize(Decimal('0.01'))
        except DiscountCode.DoesNotExist:
            # Clear invalid discount code
            if 'discount_code_id' in request.session:
                del request.session['discount_code_id']
    
    # Calculate totals
    total = sum(item.total_price() for item in cart_items)
    grand_total = total - discount_amount
    
    # Configure PayPal SDK
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET
    })
    
    # Configure Razorpay client
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    if request.method == 'POST':
        try:
            # Parse JSON data if it's an AJAX request
            shipping_data = {}
            payment_method = 'PAYPAL'  # Default
            
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
                shipping_data = data
                payment_method = data.get('payment_method', 'PAYPAL')
            
            # Create Order first (common for both payment methods)
            order = Order.objects.create(
                user=request.user,
                subtotal=total,
                discount_code=discount_code,
                discount_amount=discount_amount,
                total_price=grand_total,
                payment_method=payment_method,
                status='PENDING'
            )
            
            # Save shipping information if provided
            if shipping_data:
                order.shipping_address = f"{shipping_data.get('address', '')}, {shipping_data.get('city', '')}, {shipping_data.get('state', '')} {shipping_data.get('zipCode', '')}"
                order.recipient_name = f"{shipping_data.get('firstName', '')} {shipping_data.get('lastName', '')}"
                order.recipient_email = shipping_data.get('email', '')
                order.save()
            
            # Create OrderItems
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
            
            # Process based on payment method
            if payment_method == 'RAZORPAY':
                # Create Razorpay Order
                razorpay_order = razorpay_client.order.create({
                    'amount': int(grand_total * 100),  # Amount in paise
                    'currency': 'INR',
                    'receipt': f'order_{order.id}',
                    'payment_capture': 1  # Auto-capture
                })
                
                # Update order with Razorpay ID
                order.payment_id = razorpay_order['id']
                order.save()
                
                # Store order ID in session
                request.session['razorpay_order_id'] = razorpay_order['id']
                request.session['order_id'] = order.id
                
                # Return Razorpay order details
                payment_data = {
                    'method': 'razorpay',
                    'order_id': razorpay_order['id'],
                    'amount': int(grand_total * 100),
                    'currency': 'INR',
                    'name': 'Pharmacy Order',
                    'description': f'Order #{order.id}',
                    'key_id': settings.RAZORPAY_KEY_ID,
                    'prefill': {
                        'name': order.recipient_name or request.user.get_full_name() or request.user.username,
                        'email': order.recipient_email or request.user.email or '',
                    }
                }
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse(payment_data)
                else:
                    return render(request, 'cart/razorpay_checkout.html', payment_data)
                
            else:  # PayPal
                # Create PayPal Payment
                payment = paypalrestsdk.Payment({
                    "intent": "sale",
                    "payer": {
                        "payment_method": "paypal"
                    },
                    "redirect_urls": {
                        "return_url": request.build_absolute_uri(reverse('payment_success')),
                        "cancel_url": request.build_absolute_uri(reverse('payment_cancel'))
                    },
                    "transactions": [{
                        "amount": {
                            "total": str(round(grand_total, 2)),
                            "currency": "USD",
                            "details": {
                                "subtotal": str(round(total, 2)),
                                "discount": str(round(discount_amount, 2))
                            }
                        },
                        "description": "Pharmacy Order"
                    }]
                })

                if payment.create():
                    # Update order payment ID
                    order.payment_id = payment.id
                    order.save()
                    
                    # Store payment ID in session
                    request.session['paypal_payment_id'] = payment.id
                    request.session['order_id'] = order.id
                    
                    # Find the approval URL
                    approval_url = None
                    for link in payment.links:
                        if link.rel == "approval_url":
                            approval_url = link.href
                    
                    if approval_url:
                        if request.headers.get('Content-Type') == 'application/json':
                            return JsonResponse({'redirect_url': approval_url})
                        else:
                            return redirect(approval_url)
                    else:
                        messages.error(request, 'No PayPal approval URL found.')
                        return JsonResponse({'error': 'No approval URL found'}, status=400) if request.headers.get('Content-Type') == 'application/json' else redirect('cart')
                else:
                    # Log the detailed error
                    error_msg = f"PayPal Error: {payment.error}"
                    print(error_msg)
                    messages.error(request, f'Payment error: {error_msg}')
                    return JsonResponse({'error': error_msg}, status=400) if request.headers.get('Content-Type') == 'application/json' else redirect('cart')
                
        except Exception as e:
            # Log the exception
            error_msg = f"Payment Exception: {str(e)}"
            print(error_msg)
            messages.error(request, f'Payment error: {error_msg}')
            return JsonResponse({'error': error_msg}, status=500) if request.headers.get('Content-Type') == 'application/json' else redirect('cart')

    # Get active discount codes
    active_discount_codes = DiscountCode.objects.filter(
        active=True,
        valid_from__lte=datetime.now(),
        valid_to__gte=datetime.now()
    )

    return render(request, 'cart/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'discount_code': discount_code,
        'discount_amount': discount_amount,
        'grand_total': grand_total,
        'active_discount_codes': active_discount_codes,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    })

@login_required
def apply_discount(request):
    if request.method == 'POST':
        code = request.POST.get('discount_code')
        now = datetime.now()
        
        try:
            discount = DiscountCode.objects.get(
                code=code,
                active=True,
                valid_from__lte=now,
                valid_to__gte=now
            )
            
            # Store discount code ID in session
            request.session['discount_code_id'] = discount.id
            
            messages.success(request, f'Discount code "{code}" applied successfully!')
        except DiscountCode.DoesNotExist:
            if 'discount_code_id' in request.session:
                del request.session['discount_code_id']
            messages.error(request, 'Invalid or expired discount code.')
    
    return redirect('cart')

@login_required
def payment_success(request):
    order_id = request.session.get('order_id')
    
    if not order_id:
        messages.error(request, "No order information found.")
        return redirect('cart')
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Handle PayPal success
        if order.payment_method == 'PAYPAL':
            paypal_payment_id = request.session.get('paypal_payment_id')
            if not paypal_payment_id:
                messages.error(request, "No payment information found.")
                return redirect('cart')
                
            payment = paypalrestsdk.Payment.find(paypal_payment_id)
            payer_id = request.GET.get('PayerID')
            
            if payment.execute({"payer_id": payer_id}):
                # Payment executed successfully
                order.status = 'PAID'
                order.save()
                
                # Clear cart
                CartItem.objects.filter(user=request.user).delete()
                
                messages.success(request, 'Payment successful! Your order has been processed.')
            else:
                messages.error(request, f'Payment execution failed: {payment.error}')
                
            # Clean up session
            if 'paypal_payment_id' in request.session:
                del request.session['paypal_payment_id']
                
        # Handle Razorpay success
        elif order.payment_method == 'RAZORPAY':
            # Payment already verified by webhook or callback, just update UI
            order.status = 'PAID'
            order.save()
            
            # Clear cart
            CartItem.objects.filter(user=request.user).delete()
            
            messages.success(request, 'Payment successful! Your order has been processed.')
            
            # Clean up session
            if 'razorpay_order_id' in request.session:
                del request.session['razorpay_order_id']
                
    except Order.DoesNotExist:
        messages.error(request, "We couldn't find your order.")
    except Exception as e:
        messages.error(request, f'Error processing payment: {str(e)}')
    
    # Clean up session
    if 'order_id' in request.session:
        del request.session['order_id']
    if 'discount_code_id' in request.session:
        del request.session['discount_code_id']
        
    return redirect('home')

@login_required
def payment_cancel(request):
    order_id = request.session.get('order_id')
    
    if order_id:
        try:
            # Update order status to cancelled
            order = Order.objects.get(id=order_id)
            order.status = 'CANCELLED'
            order.save()
            
            # Clean up session
            if 'paypal_payment_id' in request.session:
                del request.session['paypal_payment_id']
            if 'razorpay_order_id' in request.session:
                del request.session['razorpay_order_id']
            if 'order_id' in request.session:
                del request.session['order_id']
            if 'discount_code_id' in request.session:
                del request.session['discount_code_id']
                
        except Exception as e:
            print(f"Error cancelling order: {str(e)}")
    
    messages.warning(request, 'Payment was cancelled.')
    return redirect('cart')

@require_POST
def razorpay_callback(request):
    # Verify the payment signature
    params_dict = {
        'razorpay_order_id': request.POST.get('razorpay_order_id'),
        'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
        'razorpay_signature': request.POST.get('razorpay_signature')
    }
    
    # Initialize Razorpay client
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Payment verification successful
        order = Order.objects.get(payment_id=params_dict['razorpay_order_id'])
        order.status = 'PAID'
        order.save()
        
        # Clear cart
        CartItem.objects.filter(user=request.user).delete()
        
        return JsonResponse({'status': 'success'})
    except:
        return JsonResponse({'status': 'failure'}, status=400)