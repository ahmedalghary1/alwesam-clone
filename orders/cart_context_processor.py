from products.models import Product, ProductVariant
from .models import Cart, CartDetail


def get_cart_data(request):
    """
    Returns cart data for navbar for both authenticated & anonymous users.
    Now uses ProductVariant instead of ProductColor.
    """

    # ================================================
    # 🔹 مستخدم مسجل → السلة من قاعدة البيانات
    # ================================================
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, status='Inprogress')
        cart_detail = CartDetail.objects.filter(cart=cart).select_related("variant", "product")

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
            product_id, variant_id = key.split('-')
        except ValueError:
            continue  # تجاهل أي مفتاح غير صالح

        # جلب المنتج والمتغير
        try:
            variant = ProductVariant.objects.select_related("product").get(id=variant_id)
            product = variant.product
        except ProductVariant.DoesNotExist:
            continue  # تجاهل العناصر التالفة

        # حساب الإجمالي
        item_total = variant.price * qty
        total_price += item_total

        cart_items.append({
            "product": product,
            "variant": variant,
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
