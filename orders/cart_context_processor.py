from .models import Cart, CartDetail


from .models import Product, ProductColor, Cart, CartDetail

def get_cart_data(request):
    """
    Returns cart data for navbar for both authenticated & anonymous users.
    """
    # ---------------------------------------------
    # 🔹 مستخدم مسجل دخول → جلب من قاعدة البيانات
    # ---------------------------------------------
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, status='Inprogress')
        cart_detail = CartDetail.objects.filter(cart=cart)
        return {
            'cart_data': cart,
            'cart_detail_data': cart_detail,
        }

    # ---------------------------------------------
    # 🔸 مستخدم غير مسجل دخول → جلب من Session
    # ---------------------------------------------
    session_cart = request.session.get('cart', {})

    cart_items = []
    total_price = 0

    for key, qty in session_cart.items():
        product_id, color_id = key.split('-')

        try:
            product = Product.objects.get(id=product_id)
            product_color = ProductColor.objects.get(id=color_id)
        except (Product.DoesNotExist, ProductColor.DoesNotExist):
            continue  # تجاهل العناصر التالفة

        item_total = product_color.price * qty
        total_price += item_total

        cart_items.append({
            "product": product,
            "color": product_color,
            "quantity": qty,
            "total": item_total,
        })

    return {
        'cart_data': {
            "total": total_price,
            "count": len(cart_items)
        },
        'cart_detail_data': cart_items,
    }
