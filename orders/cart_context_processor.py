from .models import Cart, CartDetail


def get_cart_data(request):
    """
    Context processor to get cart data for navbar.
    Returns cart and cart_detail for authenticated users.
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, status='Inprogress')
        cart_detail = CartDetail.objects.filter(cart=cart)
        return {'cart_data': cart, 'cart_detail_data': cart_detail}
    else:
        # Return empty queryset for anonymous users
        return {'cart_data': None, 'cart_detail_data': []}