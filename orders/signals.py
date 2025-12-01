from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Cart, CartDetail
from products.models import Product

@receiver(user_logged_in)
def merge_session_cart(sender, user, request, **kwargs):
    session_cart = request.session.get('cart')
    if not session_cart:
        return

    cart, _ = Cart.objects.get_or_create(user=user, status="Inprogress")

    for pid, qty in session_cart.items():
        try:
            product = Product.objects.get(id=pid)
        except Product.DoesNotExist:
            continue

        item, created = CartDetail.objects.get_or_create(cart=cart, product=product)

        # تحديث الكمية بشكل صحيح
        item.quantity += qty
        item.total = item.quantity * product.price
        item.save()

    # حذف السلة من السيشن بعد الدمج
    del request.session['cart']
