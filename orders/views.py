from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
import datetime

from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Order, OrderDetail, Cart, CartDetail, Coupon, OrderAddress
from products.models import Product ,ProductColor
from .models import DeliveryFee
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser


def checkout(request, item_id=None):

    # ===================================================
    #   تحميل السلة (مستخدم مسجل دخول)
    # ===================================================
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, status="Inprogress")
        cart_detail = CartDetail.objects.filter(cart=cart).select_related("color", "product")

        # تجاهل أي عنصر ليس لديه لون
        valid_items = [item for item in cart_detail if item.color]

        subtotal = sum(item.color.price * item.quantity for item in valid_items)

    else:
        # ===================================================
        #   Session cart للزائر
        #   المفتاح هو: "productId-colorId"
        # ===================================================
        session_cart = request.session.get("cart", {})
        cart = None
        cart_detail = []

        for key, qty in session_cart.items():
            product_id, color_id = key.split("-")

            color_obj = get_object_or_404(ProductColor, id=color_id)

            cart_detail.append({
                "id": key,
                "product": color_obj.product,
                "color": color_obj,
                "quantity": qty,
                "total": color_obj.price * qty
            })

        subtotal = sum(item["total"] for item in cart_detail)

    # ===================================================
    #   رسوم التوصيل
    # ===================================================
    deliveryFee = DeliveryFee.objects.last()
    delivery_fee = deliveryFee.fee if deliveryFee else 0
    total = subtotal + delivery_fee

    # ===================================================
    #   عمليات تعديل السلة (AJAX)
    # ===================================================
    action = request.GET.get("action")

    if action:

        # ===================================================
        #   تعديل السلة للمستخدم المسجل دخول
        # ===================================================
        if request.user.is_authenticated and item_id:

            try:
                item = CartDetail.objects.get(id=int(item_id), cart=cart)
                if action == "increase":
                    item.quantity += 1

                elif action == "decrease" and item.quantity > 1:
                    item.quantity -= 1

                elif action == "delete":
                    item.delete()
                    item = None

                if item:
                    if not item.color:
                        item.delete()
                        return JsonResponse({"success": True, "deleted": True})

                    item.total = item.color.price * item.quantity
                    item.save()

            except (CartDetail.DoesNotExist, ValueError):
                return JsonResponse({"success": False})

            # إعادة حساب الإجمالي
            cart_detail = CartDetail.objects.filter(cart=cart)
            subtotal = sum(i.color.price * i.quantity for i in cart_detail)
            total = subtotal + delivery_fee

            return JsonResponse({
                "success": True,
                "quantity": item.quantity if item else 0,
                "item_total": item.total if item else 0,
                "sub_total": subtotal,
                "deliveryFee": delivery_fee,
                "total": total
            })

        # ===================================================
        #   تعديل Session cart للزائر
        # ===================================================
        else:
            session_cart = request.session.get("cart", {})

            if item_id not in session_cart:
                return JsonResponse({"success": False})

            if action == "increase":
                session_cart[item_id] += 1

            elif action == "decrease" and session_cart[item_id] > 1:
                session_cart[item_id] -= 1

            elif action == "delete":
                del session_cart[item_id]

            request.session["cart"] = session_cart

            # إعادة الحساب
            subtotal = 0
            item_total = 0

            for key, qty in session_cart.items():
                product_id, color_id = key.split("-")
                color_obj = get_object_or_404(ProductColor, id=color_id)

                item_total_current = color_obj.price * qty
                subtotal += item_total_current

                if key == item_id:
                    item_total = item_total_current

            total = subtotal + delivery_fee

            return JsonResponse({
                "success": True,
                "quantity": session_cart.get(item_id, 0),
                "item_total": item_total,
                "sub_total": subtotal,
                "deliveryFee": delivery_fee,
                "total": total
            })

    # ===================================================
    #   عرض صفحة Checkout
    # ===================================================
    return render(request, "orders/checkout.html", {
        "cart": cart,
        "cart_detail_data": cart_detail,
        "deliveryFee": delivery_fee,
        "subtotal": subtotal,
        "total": total,
        "is_guest": not request.user.is_authenticated
    })


def add_to_cart(request):

    product_id = request.POST.get('product_id')
    color_id = request.POST.get('color_id')   # اللون المختار
    quantity = int(request.POST.get('quantity', 1))

    # التحقق من وجود اللون
    product_color = get_object_or_404(ProductColor, id=color_id)

    # ---------------------------------------------------------
    # 1) المستخدم غير مسجل دخول → Session Cart
    # ---------------------------------------------------------
    if not request.user.is_authenticated:
        session_cart = request.session.get('cart', {})

        key = f"{product_id}-{color_id}"

        # تحقق من المخزون
        if quantity > product_color.quantity:
            return JsonResponse({
                'success': False,
                'message': f"⚠️ الكمية المتوفرة من اللون {product_color.color.name} هي {product_color.quantity}",
            })

        # تحديث السلة
        if key in session_cart:
            new_qty = session_cart[key] + quantity
            if new_qty > product_color.quantity:
                return JsonResponse({'success': False, 'message': '⚠️ كمية غير متاحة'})
            session_cart[key] = new_qty
        else:
            session_cart[key] = quantity

        request.session['cart'] = session_cart

        return JsonResponse({
            'success': True,
            'message': f"🛒 تم إضافة المنتج بلون {product_color.color.name} إلى السلة",
            'cart_count': len(session_cart),
        })


    # ---------------------------------------------------------
    # 2) المستخدم مسجل دخول
    # ---------------------------------------------------------
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)

        cart, _ = Cart.objects.get_or_create(user=request.user, status='Inprogress')

        # كل عنصر بالسلة مرتبط بمنتج ولون
        cart_detail, created = CartDetail.objects.get_or_create(
            cart=cart,
            product=product,
            color=product_color
        )

        # التحقق من المخزون
        if not created:
            new_qty = cart_detail.quantity + quantity
            if new_qty > product_color.quantity:
                return JsonResponse({'success': False, 'message': '⚠️ كمية غير متاحة لهذا اللون'})
            cart_detail.quantity = new_qty
        else:
            if quantity > product_color.quantity:
                return JsonResponse({'success': False, 'message': '⚠️ كمية غير متاحة لهذا اللون'})
            cart_detail.quantity = quantity

        # الحساب الجديد
        cart_detail.total = round(product_color.price * cart_detail.quantity, 2)
        cart_detail.save()

        return JsonResponse({
            'success': True,
            'message': f"🛒 تمت إضافة المنتج بلون {product_color.color.name} إلى السلة",
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
                
                print(order,
                    cart_item.product,
                    cart_item.quantity,
                    cart_item.product.price,
                    cart_item.total)
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



