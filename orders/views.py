from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
import datetime

from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Order, OrderDetail, Cart, CartDetail, Coupon
from products.models import Product
from .models import DeliveryFee
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser

def checkout(request, item_id=None):

    # =========================
    #   تحميل السلة (مستخدم / زائر)
    # =========================
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, status="Inprogress")
        cart_detail = CartDetail.objects.filter(cart=cart)

        subtotal = sum(item.product.price * item.quantity for item in cart_detail)

    else:
        # ------ session cart ------
        session_cart = request.session.get("cart", {})
        cart = None
        cart_detail = []

        products = Product.objects.filter(id__in=session_cart.keys())

        for product in products:
            qty = session_cart[str(product.id)]
            cart_detail.append({
                "id": product.id,
                "product": product,
                "quantity": qty,
                "total": product.price * qty
            })

        subtotal = sum(item["total"] for item in cart_detail)

    # =========================
    #   رسوم التوصيل
    # =========================
    deliveryFee = DeliveryFee.objects.last()
    delivery_fee = deliveryFee.fee if deliveryFee else 0
    total = subtotal + delivery_fee

    # =========================
    #   عمليات تعديل السلة (AJAX)
    # =========================
    action = request.GET.get("action")

    if action:

        # ========== لو المستخدم مسجل دخول ==========
        if request.user.is_authenticated and item_id:

            try:
                item = CartDetail.objects.get(id=item_id, cart=cart)

                if action == "increase":
                    item.quantity += 1
                elif action == "decrease" and item.quantity > 1:
                    item.quantity -= 1
                elif action == "delete":
                    item.delete()
                    item = None

                if item:
                    item.total = item.product.price * item.quantity
                    item.save()

            except CartDetail.DoesNotExist:
                return JsonResponse({"success": False})

            # إعادة الحساب
            cart_detail = CartDetail.objects.filter(cart=cart)
            subtotal = sum(i.product.price * i.quantity for i in cart_detail)
            total = subtotal + delivery_fee

            return JsonResponse({
                "success": True,
                "quantity": item.quantity if item else 0,
                "item_total": item.total if item else 0,
                "sub_total": subtotal,
                "deliveryFee": delivery_fee,
                "total": total
            })


        # ========== تعديل session cart للزائر ==========
        else:
            session_cart = request.session.get("cart", {})

            product_id = str(item_id)
            if product_id not in session_cart:
                return JsonResponse({"success": False})

            if action == "increase":
                session_cart[product_id] += 1

            elif action == "decrease" and session_cart[product_id] > 1:
                session_cart[product_id] -= 1

            elif action == "delete":
                del session_cart[product_id]

            request.session["cart"] = session_cart

            # إعادة الحساب للزائر
            products = Product.objects.filter(id__in=session_cart.keys())
            subtotal = sum(
                Product.objects.get(id=pid).price * qty
                for pid, qty in session_cart.items()
            )
            total = subtotal + delivery_fee

            return JsonResponse({
                "success": True,
                "quantity": session_cart.get(product_id, 0),
                "item_total": (Product.objects.get(id=item_id).price * session_cart.get(product_id, 0)) if item_id in session_cart else 0,
                "sub_total": subtotal,
                "deliveryFee": delivery_fee,
                "total": total
            })


    # =========================
    #   عرض صفحة checkout
    # =========================
    return render(request, "orders/checkout.html", {
        "cart": cart,
        "cart_detail_data": cart_detail,
        "deliveryFee": delivery_fee,
        "subtotal": subtotal,
        "total": total,
        "is_guest": not request.user.is_authenticated
    })

# def add_to_cart(request):

#     if not request.user.is_authenticated:
#         login_url = reverse('accounts:login')  
#         next_param = request.build_absolute_uri()
#         return JsonResponse({
#             'login_required': True,
#             'login_url': f"{login_url}?next={next_param}",
#             'message': 'يرجى تسجيل الدخول أولاً'
#         }, status=401)

#     if request.method == 'POST':
#         product = get_object_or_404(Product, id=request.POST.get('product_id'))
#         quantity = int(request.POST.get('quantity', 1))

#         # التحقق من توفر الكمية
#         if product.quantity == 0:
#             return JsonResponse({
#                 'success': False,
#                 'out_of_stock': True,
#                 'message': '❌ عذراً، هذا المنتج غير متوفر حالياً'
#             })

#         cart, _ = Cart.objects.get_or_create(user=request.user, status='Inprogress')
#         cart_detail, created = CartDetail.objects.get_or_create(cart=cart, product=product)

#         if not created:
#             # المنتج موجود مسبقاً
#             new_quantity = cart_detail.quantity + quantity
            
#             if new_quantity > product.quantity:
#                 return JsonResponse({
#                     'success': False,
#                     'insufficient': True,
#                     'message': f'⚠️ الكمية المتوفرة من هذا المنتج: {product.quantity} قطعة فقط',
#                     'available': product.quantity,
#                     'current_in_cart': cart_detail.quantity
#                 })
            
#             cart_detail.quantity = new_quantity
#             already_exists = True
#         else:
#             if quantity > product.quantity:
#                 return JsonResponse({
#                     'success': False,
#                     'insufficient': True,
#                     'message': f'⚠️ الكمية المتوفرة من هذا المنتج: {product.quantity} قطعة فقط',
#                     'available': product.quantity
#                 })
#             cart_detail.quantity = quantity
#             already_exists = False

#         cart_detail.total = round(product.price * cart_detail.quantity, 2)
#         cart_detail.save()

#         cart_detail_list = CartDetail.objects.filter(cart=cart)
#         total = cart.cart_total
#         cart_count = cart_detail_list.count()

#         if already_exists:
#             message = f"🔄 المنتج '{product.name}' موجود مسبقاً - تم تحديث الكمية"
#         else:
#             message = f"✅ تم إضافة '{product.name}' إلى السلة بنجاح"

#         return JsonResponse({
#             'success': True,
#             'message': message,
#             'already_exists': already_exists,
#             'total': total,
#             'cart_count': cart_count,
#         })

#     return JsonResponse({'success': False, 'message': 'طريقة الطلب غير صحيحة'}, status=400)



def add_to_cart(request):

    # لو المستخدم غير مسجل دخول → استخدم session cart
    if not request.user.is_authenticated:
        session_cart = request.session.get('cart', {})

        product = get_object_or_404(Product, id=request.POST.get('product_id'))
        quantity = int(request.POST.get('quantity', 1))

        # تحقق من المخزون
        if quantity > product.quantity:
            return JsonResponse({
                'success': False,
                'message': f"⚠️ الكمية المتوفرة من '{product.name}' هي {product.quantity}",
            })

        # تحديث السلة
        if str(product.id) in session_cart:
            new_qty = session_cart[str(product.id)] + quantity
            if new_qty > product.quantity:
                return JsonResponse({'success': False, 'message': '⚠️ كمية غير متاحة'})
            session_cart[str(product.id)] = new_qty
        else:
            session_cart[str(product.id)] = quantity

        request.session['cart'] = session_cart

        return JsonResponse({
            'success': True,
            'message': f"🛒 تم إضافة {product.name} إلى السلة",
            'cart_count': len(session_cart),
        })

    # ---------- المستخدم المسجل دخول ----------
    if request.method == 'POST':
        product = get_object_or_404(Product, id=request.POST.get('product_id'))
        quantity = int(request.POST.get('quantity', 1))

        cart, _ = Cart.objects.get_or_create(user=request.user, status='Inprogress')
        cart_detail, created = CartDetail.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_detail.quantity += quantity
        else:
            cart_detail.quantity = quantity

        cart_detail.total = round(product.price * cart_detail.quantity, 2)
        cart_detail.save()

        return JsonResponse({
            'success': True,
            'message': f"🛒 تم إضافة {product.name} إلى السلة",
            'cart_count': CartDetail.objects.filter(cart=cart).count(),
        })

    return JsonResponse({'success': False})


@login_required
def create_order(request):
    """
    Create order from cart with COD (Cash on Delivery).
    """
    if request.method == 'POST':
        # Get cart
        try:
            cart = Cart.objects.get(user=request.user, status='Inprogress')
            cart_detail = CartDetail.objects.filter(cart=cart)
            
            if not cart_detail.exists():
                messages.error(request, '❌ السلة فارغة.')
                return redirect('checkout')
            
        except Cart.DoesNotExist:
            messages.error(request, '❌ السلة غير موجودة.')
            return redirect('checkout')
        
        # Get form data
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        customer_email = request.POST.get('customer_email', request.user.email if request.user.is_authenticated else '')
        governorate = request.POST.get('governorate')
        city = request.POST.get('city', '')
        address_line = request.POST.get('address')
        notes = request.POST.get('notes', '')
        
        # Validation
        if not all([customer_name, customer_phone, governorate, address_line]):
            messages.error(request, '❌ يرجى ملء جميع الحقول المطلوبة.')
            return redirect('orders:checkout')
        
        # التحقق من توفر الكمية لجميع المنتجات في السلة
        for cart_item in cart_detail:
            if cart_item.quantity > cart_item.product.quantity:
                messages.error(
                    request, 
                    f'❌ عذراً، الكمية المتوفرة من "{cart_item.product.name}" هي {cart_item.product.quantity} فقط. '
                    f'يرجى تعديل الكمية في السلة.'
                )
                return redirect('orders:checkout')
        
        try:
            # Create order address
            order_address = OrderAddress.objects.create(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                governorate=governorate,
                city=city,
                address_line=address_line,
                notes=notes
            )
            
            # Get delivery fee
            delivery_fee_obj = DeliveryFee.objects.last()
            delivery_fee = delivery_fee_obj.fee if delivery_fee_obj else 0
            
            # Create order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                address=order_address,
                status='Received',
                delivery_fee=delivery_fee
            )
            
            # Create order details from cart
            for cart_item in cart_detail:
                OrderDetail.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    total=cart_item.total
                )
                
                # إنقاص الكمية من المخزون
                product = cart_item.product
                product.quantity -= cart_item.quantity
                product.save()
            
            # Calculate and save order total
            order.calculate_total()
            order.save()
            
            # Mark cart as completed
            cart.status = 'Completed'
            cart.save()
            
            messages.success(request, f'✅ تم إنشاء الطلب بنجاح! رقم الطلب: {order.code}')
            return redirect('orders:order_success', order_code=order.code)
            
        except Exception as e:
            messages.error(request, f'❌ حدث خطأ أثناء إنشاء الطلب: {str(e)}')
            return redirect('orders:checkout')
    
    return redirect('orders:checkout')


def order_success(request, order_code):
    """
    Display order success page.
    """
    order = get_object_or_404(Order, code=order_code)
    order_details = OrderDetail.objects.filter(order=order)
    
    return render(request, 'orders/order_success.html', {
        'order': order,
        'order_details': order_details
    })


@login_required
def my_orders(request):
    """
    Display user's orders.
    """
    orders = Order.objects.filter(user=request.user).order_by('-order_time')
    
    return render(request, 'orders/my_orders.html', {
        'orders': orders
    })


@login_required
def order_detail_view(request, order_code):
    """
    Display order details.
    """
    order = get_object_or_404(Order, code=order_code, user=request.user)
    order_details = OrderDetail.objects.filter(order=order)
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_details': order_details
    })



