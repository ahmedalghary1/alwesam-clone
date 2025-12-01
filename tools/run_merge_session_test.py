"""
Quick script to simulate merging a session cart for a user and verify no NameError.
Run: & "E:/web dev/alwesam/Scripts/python.exe" tools/run_merge_session_test.py
"""
import os
from types import SimpleNamespace

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()

from accounts.models import CustomUser
from products.models import Product
from orders.models import Cart, CartDetail
from orders.signals import merge_session_cart


def run():
    """Create a user and product, call `merge_session_cart` and print the resulting cart items."""
    # Create test user
    email = 'merge_test_user@example.com'
    user, created = CustomUser.objects.get_or_create(email=email)
    if created:
        user.set_password('test123456')
        user.save()

    # Create or get test product
    product, pcreated = Product.objects.get_or_create(name='Merge Test Product', defaults={'price': 9.99, 'quantity': 10})

    # Prepare fake request
    class FakeRequest(SimpleNamespace):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.session = kwargs.get('session', {})

    # Clear any existing cart and set up an initial cart for merge test
    Cart.objects.filter(user=user, status='Inprogress').delete()
    initial_cart = Cart.objects.create(user=user, status='Inprogress')
    # Add an existing item so we can test increment behavior
    CartDetail.objects.filter(cart=initial_cart, product=product).delete()
    CartDetail.objects.create(cart=initial_cart, product=product, quantity=2, total=product.price * 2)

    session_data = {'cart': {str(product.id): '3'}}
    request = FakeRequest(session=session_data)

    # Call the function (session's cart contains 3 units)
    merge_session_cart(None, user, request)

    # Verify results
    cart = Cart.objects.filter(user=user, status='Inprogress').first()
    if cart is None:
        print('No cart found after merge')
    else:
        items = CartDetail.objects.filter(cart=cart)
        for it in items:
            print(f'CartItem: product={it.product.name}, quantity={it.quantity}, total={it.total}')

    print('Completed merge test')


if __name__ == '__main__':
    run()
