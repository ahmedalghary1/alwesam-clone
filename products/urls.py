from django.urls import path
from .views import (
    ProductDetail, 
    ProductListView, 
    CategoryListView,
    CategoryProductsView,
    add_review, 
    delete_review
)


app_name='products'

urlpatterns=[
    # الصفحة الرئيسية للمنتجات تعرض جميع الأقسام
    path('', CategoryListView.as_view(), name='product_list'),
    
    # URLs الأقسام
    path('categories/', CategoryListView.as_view(), name='categories_list'),
    path('category/<str:slug>/', CategoryProductsView.as_view(), name='category_products'),
    
    # Reviews
    path('reviews/<int:review_id>/delete/', delete_review, name='delete_review'),
    path('<path:slug>/reviews-add/', add_review, name='add_review'),
    path('<path:slug>', ProductDetail.as_view(), name='product_detail'),
]