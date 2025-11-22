from django.urls import path
from .views import checkout, add_to_cart, create_order, order_success, my_orders, order_detail_view


app_name = 'orders'
urlpatterns = [
    path('', my_orders, name='my_orders'),
    path('checkout/', checkout, name='checkout'),
    path('checkout/update/<int:item_id>/', checkout, name='checkout-update'),
    path('add-to-cart', add_to_cart, name='add-to-cart'),
    path('create-order/', create_order, name='create-order'),
    path('success/<str:order_code>/', order_success, name='order_success'),
    path('detail/<str:order_code>/', order_detail_view, name='order-detail'),
]

