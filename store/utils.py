import json
from . models import *

def cookieCart(request):
    try:
        cart = json.loads(request.COOKIES['cart'])
        print('✅ Cart from cookie:', cart)
    except KeyError:
        print('❌ No cart cookie found - creating empty cart')
        cart = {}
    except Exception as e:
        print('❌ Error loading cart cookie:', e)
        cart = {}
        
    items = []
    order = {'get_cart_total':0, 'get_cart_items':0, 'shipping':False}

    cartItems = order['get_cart_items']

    for i in cart:
        try:
            cartItems += cart[i]["quantity"]

            product = Product.objects.get(id=i)
            total = (product.price * cart[i]["quantity"])

            order['get_cart_total'] += total
            order['get_cart_items'] += cart[i]["quantity"]

            item = {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'imageURL': product.imageURL,
                },
                'quantity': cart[i]["quantity"],
                'get_total': total
            }
            items.append(item)

            if product.digital == False:
                order['shipping'] = True

        except:
            pass
    return {'cartItems':cartItems, 'order':order, 'items':items}

def cartData(request):
    if request.user.is_authenticated:
        
        print("✅ User is authenticated:", request.user.username)

        try:
            customer = request.user.customer
            print("✅ Customer found:", customer.name)
        except Exception as e:
            print("❌ Error getting customer:", e)
            customer = None

        try:
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            print("✅ Order retrieved or created:", order.id)
            print("✅ Order created newly?", created)
        except Exception as e:
            print("❌ Error getting/creating order:", e)
            order = None

        try:
            items = order.orderitem_set.all()

            cartItems = order.get_cart_items
            print(f"✅ Found {items.count()} item(s) in order.")
            for item in items:
                print("🛍️", item.product.name, "x", item.quantity)
        except Exception as e:
            print("❌ Error fetching order items:", e)
            items = []
    else:
        print("❌ User not authenticated.")
        
        cookieData = cookieCart(request)
        cartItems = cookieData['cartItems']
        order = cookieData['order']
        items = cookieData['items']
    return{'cartItems':cartItems, 'order':order, 'items':items}

def guestOrder(request, data):
    print('user is not logged in')

    print('COOKIES:', request.COOKIES)
    name = data['form']['name']
    email = data['form']['email']

    cookiData = cookieCart(request)
    items = cookiData['items']

    customer, created = Customer.objects.get_or_create(
        email=email,
    )
    customer.name = name
    customer.save()

    order = Order.objects.create(
        customer=customer,
        complete=False,
    )

    for item in items:
        product = Product.objects.get(id=item['product']['id'])

        orderItem = OrderItem.objects.create(
            product=product,
            order=order,
            quantity=item['quantity']
        )

    return customer, order