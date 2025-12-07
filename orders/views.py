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
    """
    Checkout page and AJAX handlers for updating cart quantities.
    Uses ProductVariant for price/quantity.
    """

    # ==========================
    #  تحميل السلة (مستخدم مسجل)
    # ==========================
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, status="Inprogress")
        cart_detail_qs = CartDetail.objects.filter(cart=cart).select_related("variant", "product")

        # تجاهل العناصر التي ليس لديها variant
        valid_items = [item for item in cart_detail_qs if item.variant]
        subtotal = sum(item.variant.price * item.quantity for item in valid_items)

        cart_detail_data = cart_detail_qs

    else:
        # ==========================
        #  Session cart للزائر
        # ==========================
        session_cart = request.session.get("cart", {})
        cart = None
        cart_detail_data = []

        for key, qty in session_cart.items():
            try:
                product_id, variant_id = key.split("-")
            except ValueError:
                continue

            # الحصول على الـ variant
            variant = ProductVariant.objects.filter(id=variant_id).select_related("product").first()
            if not variant:
                continue

            cart_detail_data.append({
                "id": key,
                "product": variant.product,
                "variant": variant,
                "quantity": qty,
                "total": variant.price * qty
            })

        subtotal = sum(item["total"] for item in cart_detail_data)

    # ==========================
    # رسوم التوصيل
    # ==========================
    delivery_fee = _get_delivery_fee_value()
    total = subtotal + delivery_fee

    # ==========================
    # عمليات تعديل السلة (AJAX)
    # ==========================
    action = request.GET.get("action")

    if action:

        # --------------------------
        # تعديل السلة للمستخدم المسجل
        # --------------------------
        if request.user.is_authenticated and item_id:
            try:
                item = CartDetail.objects.get(id=int(item_id), cart=cart)
            except (CartDetail.DoesNotExist, ValueError):
                return JsonResponse({"success": False})

            if action == "increase":
                # تحقق من المخزون
                if item.variant and item.quantity + 1 > item.variant.quantity:
                    return JsonResponse({"success": False, "error": _("⚠️ كمية غير متاحة")})
                item.quantity += 1

            elif action == "decrease":
                if item.quantity > 1:
                    item.quantity -= 1

            elif action == "delete":
                item.delete()
                item = None

            if item:
                # لو اختفى الـ variant → احذف العنصر
                if not item.variant:
                    item.delete()
                    return JsonResponse({"success": True, "deleted": True})

                item.total = round(item.variant.price * item.quantity, 2)
                item.save()

            # إعادة حساب الإجمالي
            cart_detail_qs = CartDetail.objects.filter(cart=cart).select_related("variant")
            subtotal = sum(i.variant.price * i.quantity for i in cart_detail_qs)
            total = subtotal + delivery_fee

            return JsonResponse({
                "success": True,
                "quantity": item.quantity if item else 0,
                "item_total": item.total if item else 0,
                "sub_total": round(subtotal, 2),
                "deliveryFee": delivery_fee,
                "total": round(total, 2)
            })

        # --------------------------------
        # تعديل Session cart للزائر
        # --------------------------------
        else:
            session_cart = request.session.get("cart", {})

            if item_id not in session_cart:
                return JsonResponse({"success": False})

            if action == "increase":
                # فحص المخزون قبل الزيادة
                key = item_id
                product_id, variant_id = key.split("-")
                variant = ProductVariant.objects.filter(id=variant_id).first()
                if not variant:
                    return JsonResponse({"success": False})
                if session_cart[item_id] + 1 > variant.quantity:
                    return JsonResponse({"success": False, "error": _("⚠️ كمية غير متاحة")})
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
                product_id, variant_id = key.split("-")
                variant = ProductVariant.objects.filter(id=variant_id).first()
                if not variant:
                    continue
                item_total_current = variant.price * qty
                subtotal += item_total_current

                if key == item_id:
                    item_total = item_total_current

            total = subtotal + delivery_fee

            return JsonResponse({
                "success": True,
                "quantity": session_cart.get(item_id, 0),
                "item_total": round(item_total, 2),
                "sub_total": round(subtotal, 2),
                "deliveryFee": delivery_fee,
                "total": round(total, 2)
            })

    # ==========================
    # عرض صفحة Checkout
    # ==========================
    return render(request, "orders/checkout.html", {
        "cart": cart,
        "cart_detail_data": cart_detail_data,
        "deliveryFee": delivery_fee,
        "subtotal": round(subtotal, 2),
        "total": round(total, 2),
        "is_guest": not request.user.is_authenticated
    })


def add_to_cart(request):
    """
    إضافة عنصر إلى السلة (AJAX expected).
    Request POST fields:
     - product_id
     - variant_id (optional; if not provided pick default)
     - quantity
    """

    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))

    # 1) تحقق من المنتج
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('❌ المنتج غير موجود.')
        }, status=400)

    # 2) اختيار الـ variant
    if not variant_id or not str(variant_id).isdigit():
        default_variant = ProductVariant.objects.filter(product=product).first()
        if default_variant:
            variant = default_variant
            variant_id = default_variant.id
        else:
            return JsonResponse({
                'success': False,
                'message': _("⚠️ لا يوجد متغيرات (variants) متاحة لهذا المنتج.")
            }, status=400)
    else:
        try:
            variant = ProductVariant.objects.get(id=variant_id, product=product)
        except ProductVariant.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _("❌ المتغير المحدد غير موجود لهذا المنتج.")
            }, status=400)

    # 3) التحقق من الكمية المتاحة
    if quantity > variant.quantity:
        return JsonResponse({
            'success': False,
            'message': _('⚠️ الكمية المتاحة فقط هي %(qty)s') % {'qty': variant.quantity}
        })

    # ====================================================
    #  المستخدم غير مسجل -> session cart
    # ====================================================
    if not request.user.is_authenticated:
        session_cart = request.session.get('cart', {})
        key = _session_key_for(product.id, variant.id)

        # تحديث السلة
        if key in session_cart:
            new_qty = session_cart[key] + quantity
            if new_qty > variant.quantity:
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
        variant=variant
    )

    if not created:
        new_qty = cart_detail.quantity + quantity
        if new_qty > variant.quantity:
            return JsonResponse({'success': False, 'message': _('⚠️ كمية غير متاحة')})
        cart_detail.quantity = new_qty
    else:
        if quantity > variant.quantity:
            return JsonResponse({'success': False, 'message': _('⚠️ كمية غير متاحة')})
        cart_detail.quantity = quantity

    cart_detail.total = round(variant.price * cart_detail.quantity, 2)
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
        cart_items = CartDetail.objects.filter(cart=cart).select_related('variant', 'product')
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
        if item.quantity > item.variant.quantity:
            messages.error(request, _(
                '❌ عذراً، الكمية المتوفرة من "%(product)s" (المتغير: %(variant)s) هي %(qty)s فقط.'
            ) % {
                'product': item.product.name,
                'variant': item.variant.name if item.variant else _('N/A'),
                'qty': item.variant.quantity if item.variant else 0
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
            quantity = item.quantity
            variant = item.variant

            OrderDetail.objects.create(
                order=order,
                product=item.product,
                variant=variant,
                quantity=quantity,
                price=variant.price,
                total=round(variant.price * quantity, 2)
            )

            # reduce stock
            variant.quantity = max(variant.quantity - quantity, 0)
            variant.save()

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
    order_details = OrderDetail.objects.filter(order=order).select_related('variant', 'product')

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
    order_details = OrderDetail.objects.filter(order=order).select_related('variant', 'product')

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_details': order_details
    })
