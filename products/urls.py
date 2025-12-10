from django.urls import path
from .views import ProductDetail, ProductListView, add_review, delete_review


app_name='products'

urlpatterns=[
    path('', ProductListView.as_view(), name='product_list'),
    path('<path:slug>', ProductDetail.as_view(), name='product_detail'),
    
    # Reviews
    path('<path:slug>/reviews/add/', add_review, name='add_review'),
    path('reviews/<int:review_id>/delete/', delete_review, name='delete_review'),
]