from django.utils.translation import gettext as _
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
import datetime

from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Order, OrderDetail, Cart, CartDetail, Coupon, OrderAddress, DeliveryFee
from products.models import Product, ProductVariant, ProductVariantImage
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser


def _get_delivery_fee_value():
    delivery_fee_obj = DeliveryFee.objects.last()
    return delivery_fee_obj.fee if delivery_fee_obj else 0


def _session_key_for(product_id, variant_id):
    """مفتاح تخزين العنصر في الجلسة: 'productId-variantId'"""
    return f"{product_id}-{variant_id}"

def checkout(request, item_id=None):

    # ========== مستخدم مسجل ==========
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, status="Inprogress")
        cart_items_raw = CartDetail.objects.filter(cart=cart).select_related(
            "variant_color", "variant_color__variant", "variant_color__color", "product"
        )

        cart_detail_data = []
        subtotal = 0

        for item in cart_items_raw:
            if not item.variant_color:
                continue

            cart_detail_data.append({
                "id": item.id,
                "product": item.product,
                "variant_color": item.variant_color,
                "quantity": item.quantity,
                "price": item.variant_color.price,
                "total": item.variant_color.price * item.quantity
            })

            subtotal += item.variant_color.price * item.quantity

    # ========== زائر (سلة Session) ==========
    else:
        from products.models import VariantColor
        session_cart = request.session.get("cart", {})
        cart_detail_data = []
        subtotal = 0

        for key, qty in session_cart.items():
            try:
                product_id, variant_color_id = key.split("-")
            except ValueError:
                continue

            variant_color = VariantColor.objects.select_related("variant", "color", "variant__product").filter(id=variant_color_id).first()
            if not variant_color:
                continue

            total_price = variant_color.price * qty

            cart_detail_data.append({
                "id": key,
                "product": variant_color.variant.product,
                "variant_color": variant_color,
                "quantity": qty,
                "price": variant_color.price,
                "total": total_price
            })

            subtotal += total_price

    # ========== رسوم الشحن ==========
    delivery_fee = _get_delivery_fee_value()
    total = subtotal + delivery_fee

    # ========== عمليات AJAX ==========
    action = request.GET.get("action")

    if action:

        # ------- مستخدم مسجل -------
        if request.user.is_authenticated and item_id:
            try:
                item = CartDetail.objects.select_related("variant_color").get(id=int(item_id), cart=cart)
            except:
                return JsonResponse({"success": False})

            if action == "increase":
                if item.quantity + 1 > item.variant_color.quantity:
                    return JsonResponse({"success": False, "error": _("⚠️ كمية غير متاحة")})
                item.quantity += 1

            elif action == "decrease" and item.quantity > 1:
                item.quantity -= 1

            elif action == "delete":
                item.delete()
                deleted = True
            else:
                deleted = False

            if action != "delete":
                item.save()
                deleted = False

            subtotal = sum(i.variant_color.price * i.quantity for i in CartDetail.objects.filter(cart=cart) if i.variant_color)

            return JsonResponse({
                "success": True,
                "deleted": deleted,
                "quantity": item.quantity if action != "delete" else 0,
                "item_total": item.variant_color.price * item.quantity if action != "delete" else 0,
                "sub_total": subtotal,
                "deliveryFee": delivery_fee,
                "total": subtotal + delivery_fee
            })

        # ------- زائر -------
        else:
            session_cart = request.session.get("cart", {})

            if item_id not in session_cart:
                return JsonResponse({"success": False})

            if action == "increase":
                product_id, variant_color_id = item_id.split("-")
                from products.models import VariantColor
                variant_color = VariantColor.objects.filter(id=variant_color_id).first()
                if session_cart[item_id] + 1 > variant_color.quantity:
                    return JsonResponse({"success": False, "error": _("⚠️ كمية غير متاحة")})
                session_cart[item_id] += 1

            elif action == "decrease" and session_cart[item_id] > 1:
                session_cart[item_id] -= 1

            elif action == "delete":
                del session_cart[item_id]

            request.session["cart"] = session_cart

            subtotal = 0
            item_total = 0

            for key, qty in session_cart.items():
                product_id, variant_color_id = key.split("-")
                variant_color = VariantColor.objects.filter(id=variant_color_id).first()
                subtotal += variant_color.price * qty
                if key == item_id:
                    item_total = variant_color.price * qty

            return JsonResponse({
                "success": True,
                "quantity": session_cart.get(item_id, 0),
                "item_total": item_total,
                "sub_total": subtotal,
                "deliveryFee": delivery_fee,
                "total": subtotal + delivery_fee
            })

    # ======= إرجاع الصفحة ========
    return render(request, "orders/checkout.html", {
        "cart_detail_data": cart_detail_data,
        "deliveryFee": delivery_fee,
        "subtotal": subtotal,
        "total": total,
        "is_guest": not request.user.is_authenticated
    })



def add_to_cart(request):
    """
    إضافة عنصر إلى السلة (AJAX expected).
    Request POST fields:
     - product_id
     - variant_color_id (required)
     - quantity
    """
    
    from products.models import VariantColor

    product_id = request.POST.get('product_id')
    variant_color_id = request.POST.get('variant_color_id')
    quantity = int(request.POST.get('quantity', 1))

    # 1) تحقق من المنتج
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('❌ المنتج غير موجود.')
        }, status=400)

    # 2) اختيار الـ variant_color
    if not variant_color_id or not str(variant_color_id).isdigit():
        return JsonResponse({
            'success': False,
            'message': _("⚠️ يجب اختيار نمط ولون.")
        }, status=400)
    
    try:
        variant_color = VariantColor.objects.select_related('variant', 'color').get(
            id=variant_color_id,
            variant__product=product
        )
    except VariantColor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _("❌ النمط أو اللون المحدد غير موجود.")
        }, status=400)

    # 3) التحقق من الكمية المتاحة
    if quantity > variant_color.quantity:
        return JsonResponse({
            'success': False,
            'message': _('⚠️ الكمية المتاحة فقط هي %(qty)s') % {'qty': variant_color.quantity}
        })

    # ====================================================
    #  المستخدم غير مسجل -> session cart
    # ====================================================
    if not request.user.is_authenticated:
        session_cart = request.session.get('cart', {})
        key = f"{product.id}-{variant_color.id}"

        # تحديث السلة
        if key in session_cart:
            new_qty = session_cart[key] + quantity
            if new_qty > variant_color.quantity:
                return JsonResponse({'success': False, 'message': _('⚠️ كمية غير متاحة')})
            session_cart[key] = new_qty
        else:
            session_cart[key] = quantity

        request.session['cart'] = session_cart

        return JsonResponse({
            'success': True,
            'message': _('🛒 تم إضافة المنتج إلى السلة'),
            'cart_count': sum(session_cart.values())
        })

    # ====================================================
    #  المستخدم مسجل -> DB cart
    # ====================================================
    cart, created_cart = Cart.objects.get_or_create(user=request.user, status='Inprogress')

    cart_detail, created = CartDetail.objects.get_or_create(
        cart=cart,
        product=product,
        variant_color=variant_color
    )

    if not created:
        new_qty = cart_detail.quantity + quantity
        if new_qty > variant_color.quantity:
            return JsonResponse({'success': False, 'message': _('⚠️ كمية غير متاحة')})
        cart_detail.quantity = new_qty
    else:
        if quantity > variant_color.quantity:
            return JsonResponse({'success': False, 'message': _('⚠️ كمية غير متاحة')})
        cart_detail.quantity = quantity

    cart_detail.total = round(variant_color.price * cart_detail.quantity, 2)
    cart_detail.save()

    return JsonResponse({
        'success': True,
        'message': _('🛒 تمت إضافة المنتج إلى السلة'),
        'cart_count': CartDetail.objects.filter(cart=cart).count(),
    })


@login_required
def create_order(request):
    """
    Create order from cart (Cash on Delivery).
    """

    if request.method != 'POST':
        return redirect('orders:checkout')

    # Get cart and details
    try:
        cart = Cart.objects.get(user=request.user, status='Inprogress')
        cart_items = CartDetail.objects.filter(cart=cart).select_related('variant_color', 'variant_color__variant', 'variant_color__color', 'product')
        if not cart_items.exists():
            messages.error(request, _('❌ السلة فارغة.'))
            return redirect('orders:checkout')
    except Cart.DoesNotExist:
        messages.error(request, _('❌ السلة غير موجودة.'))
        return redirect('orders:checkout')

    # Form data
    customer_name = request.POST.get('customer_name')
    customer_phone = request.POST.get('customer_phone')
    customer_email = request.POST.get('customer_email', request.user.email if request.user.is_authenticated else '')
    governorate = request.POST.get('governorate')
    city = request.POST.get('city', '')
    address_line = request.POST.get('address')
    notes = request.POST.get('notes', '')

    # Basic validation
    if not all([customer_name, customer_phone, governorate, address_line]):
        messages.error(request, _('❌ يرجى ملء جميع الحقول المطلوبة.'))
        return redirect('orders:checkout')

    # Check stock for all items
    for item in cart_items:
        if not item.variant_color:
            continue
        if item.quantity > item.variant_color.quantity:
            messages.error(request, _(
                '❌ عذراً، الكمية المتوفرة من "%(product)s" (%(variant)s - %(color)s) هي %(qty)s فقط.'
            ) % {
                'product': item.product.name,
                'variant': item.variant_color.variant.name,
                'color': item.variant_color.color.name,
                'qty': item.variant_color.quantity
            })
            return redirect('orders:checkout')

    try:
        # create address
        order_address = OrderAddress.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            governorate=governorate,
            city=city,
            address_line=address_line,
            notes=notes
        )

        # delivery fee
        delivery_fee_value = _get_delivery_fee_value()

        # create order header
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            address=order_address,
            status='Received',
            delivery_fee=delivery_fee_value
        )

        # create details and subtract stock
        for item in cart_items:
            if not item.variant_color:
                continue
                
            quantity = item.quantity
            variant_color = item.variant_color

            OrderDetail.objects.create(
                order=order,
                product=item.product,
                variant_color=variant_color,
                quantity=quantity,
                price=variant_color.price,
                total=round(variant_color.price * quantity, 2)
            )

            # reduce stock
            variant_color.quantity = max(variant_color.quantity - quantity, 0)
            variant_color.save()

        # calculate totals
        order.calculate_total()
        order.save()

        # mark cart completed
        cart.status = 'Completed'
        cart.save()

        messages.success(request, _('✅ تم إنشاء الطلب بنجاح! رقم الطلب: %(code)s') % {'code': order.code})
        return redirect('orders:order_success', order_code=order.code)

    except Exception as e:
        messages.error(request, _('❌ حدث خطأ أثناء إنشاء الطلب: %(error)s') % {'error': str(e)})
        return redirect('orders:checkout')


def order_success(request, order_code):
    order = get_object_or_404(Order, code=order_code)
    order_details = OrderDetail.objects.filter(order=order).select_related('variant_color', 'variant_color__variant', 'variant_color__color', 'product')

    return render(request, 'orders/order_success.html', {
        'order': order,
        'order_details': order_details
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_time')

    return render(request, 'orders/my_orders.html', {
        'orders': orders
    })


@login_required
def order_detail_view(request, order_code):
    order = get_object_or_404(Order, code=order_code, user=request.user)
    order_details = OrderDetail.objects.filter(order=order).select_related('variant_color', 'variant_color__variant', 'variant_color__color', 'product')

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_details': order_details
    })


@login_required
def delete_order(request, order_code):
    """
    حذف طلب (للعميل فقط - الطلبات التي لم يتم شحنها بعد)
    """
    order = get_object_or_404(Order, code=order_code, user=request.user)
    
    # السماح بالحذف فقط للطلبات التي لم يتم شحنها
    if order.status in ['Shipped', 'Delivered']:
        messages.error(request, _('❌ لا يمكن حذف الطلب بعد الشحن. يرجى التواصل مع خدمة العملاء.'))
        return redirect('orders:my_orders')
    
    if request.method == 'POST':
        order_code_display = order.code
        order.delete()
        messages.success(request, _('✅ تم حذف الطلب #%(code)s بنجاح') % {'code': order_code_display})
        return redirect('orders:my_orders')
    
    return redirect('orders:my_orders')
