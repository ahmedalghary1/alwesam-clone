from django.urls import path
from .views import ProductDetail, ProductListView


app_name='products'

urlpatterns=[

    path('', ProductListView.as_view(),name='product_list'),
    path('<path:slug>', ProductDetail.as_view(),name='product_detail'),
    
  
]