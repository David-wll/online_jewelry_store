from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import json
import datetime

from .models import *
from .utils import cookieCart, guestOrder, cartData


def home(request):
    context = {}
    return render(request, 'store/home.html')


def store(request):
    data = cartData(request)
    cartItems = data['cartItems']

    try:
        products = Product.objects.all()
        print("PRODUCTS:", products)
    except Exception as e:
        print("ERROR:", e)
        products = []
    
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def cart(request):
    print("🔍 DEBUG: Cart view accessed")

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


@csrf_exempt
def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    
    print('Action:', action)
    print('productId:', productId)

    # Check if user is authenticated
    if request.user.is_authenticated:
        try:
            customer = request.user.customer
            product = Product.objects.get(id=productId)
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            
            orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
            
            if action == 'add':
                orderItem.quantity = (orderItem.quantity + 1)
            elif action == 'remove':
                orderItem.quantity = (orderItem.quantity - 1)
            
            orderItem.save()
            
            if orderItem.quantity <= 0:
                orderItem.delete()
            
            print(f"✅ Item updated: {product.name} - Quantity: {orderItem.quantity if orderItem.quantity > 0 else 0}")
            return JsonResponse('Item was added', safe=False)
        except Exception as e:
            print(f"❌ Error updating item: {e}")
            return JsonResponse(f'Error: {str(e)}', safe=False, status=400)
    else:
        # For guest users, return message to handle via cookies in frontend
        print("⚠️ Guest user - handle via cookies")
        return JsonResponse('Item updated in cookie', safe=False)


@csrf_exempt
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transation_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment complete', safe=False)


def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            print(f"✅ User logged in: {user.username}")
            
            # Ensure customer exists
            try:
                customer = user.customer
                print(f"✅ Customer exists: {customer.name}")
            except Customer.DoesNotExist:
                print("⚠️ Customer doesn't exist, creating one...")
                Customer.objects.create(user=user, name=user.username, email=user.email)
            
            # Migrate cookie cart to database cart
            migrate_cookie_cart_to_db(request, user)
            return redirect('store')
        else:
            return render(request, 'store/login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'store/login.html')


def registerPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        print(f"✅ User created: {username}")
        
        # Ensure customer is created (signal should handle this, but let's be safe)
        customer, created = Customer.objects.get_or_create(
            user=user,
            defaults={'name': username, 'email': email}
        )
        if created:
            print(f"✅ Customer created via manual call: {customer.name}")
        else:
            print(f"✅ Customer already exists (created by signal): {customer.name}")
        
        login(request, user)
        
        # Migrate any cookie cart items to the new user's cart
        migrate_cookie_cart_to_db(request, user)
        
        return redirect('store')

    return render(request, 'store/register.html')


def logoutUser(request):
    logout(request)
    return redirect('store')


# Helper function to migrate cookie cart to database
def migrate_cookie_cart_to_db(request, user):
    """
    Migrate items from cookie cart to database cart when user logs in
    """
    try:
        cart = json.loads(request.COOKIES.get('cart', '{}'))
        
        if cart:
            customer = user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            
            migrated_count = 0
            for product_id, item_data in cart.items():
                try:
                    product = Product.objects.get(id=product_id)
                    orderItem, created = OrderItem.objects.get_or_create(
                        order=order,
                        product=product
                    )
                    # Add the quantity from cookie to existing quantity
                    orderItem.quantity += item_data['quantity']
                    orderItem.save()
                    migrated_count += 1
                    print(f"✅ Migrated: {product.name} x {item_data['quantity']}")
                except Product.DoesNotExist:
                    print(f"⚠️ Product {product_id} not found, skipping")
                    continue
            
            print(f"✅ Successfully migrated {migrated_count} item(s) from cookie to database")
        else:
            print("ℹ️ No items in cookie cart to migrate")
    except Exception as e:
        print(f"❌ Error migrating cart: {e}")