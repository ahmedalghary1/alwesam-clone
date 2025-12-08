from products.models import Product, ProductVariant, VariantColor
from .models import Cart, CartDetail


def get_cart_data(request):
    """
    Returns cart data for navbar for both authenticated & anonymous users.
    Now uses VariantColor instead of ProductVariant.
    """

    # ================================================
    # 🔹 مستخدم مسجل → السلة من قاعدة البيانات
    # ================================================
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, status='Inprogress')
        cart_detail = CartDetail.objects.filter(cart=cart).select_related("variant_color", "variant_color__variant", "variant_color__color", "product")

        return {
            'cart_data': cart,
            'cart_detail_data': cart_detail,
        }

    # ================================================
    # 🔸 مستخدم غير مسجل → Session cart
    # ================================================
    session_cart = request.session.get('cart', {})

    cart_items = []
    total_price = 0

    for key, qty in session_cart.items():
        try:
            product_id, variant_color_id = key.split('-')
        except ValueError:
            continue  # تجاهل أي مفتاح غير صالح

        # جلب المنتج والمتغير
        try:
            variant_color = VariantColor.objects.select_related("variant", "color", "variant__product").get(id=variant_color_id)
            product = variant_color.variant.product
        except VariantColor.DoesNotExist:
            continue  # تجاهل العناصر التالفة

        # حساب الإجمالي
        item_total = variant_color.price * qty
        total_price += item_total

        cart_items.append({
            "product": product,
            "variant_color": variant_color,
            "quantity": qty,
            "total": item_total,
        })

    return {
        'cart_data': {
            "total": total_price,
            "count": sum(item["quantity"] for item in cart_items)
        },
        'cart_detail_data': cart_items,
    }
