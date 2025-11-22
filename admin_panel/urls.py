from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # Products Management
    path('products/', views.admin_products_list, name='products-list'),
    path('products/create/', views.admin_product_create, name='product-create'),
    path('products/edit/<int:product_id>/', views.admin_product_edit, name='product-edit'),
    path('products/delete/<int:product_id>/', views.admin_product_delete, name='product-delete'),
    
    # Orders Management
    path('orders/', views.admin_orders_list, name='orders-list'),
    path('orders/<str:order_code>/', views.admin_order_detail, name='order-detail'),
    
    # Users Management
    path('users/', views.admin_users_list, name='users-list'),
    
    # Categories Management
    path('categories/', views.admin_categories_list, name='categories-list'),
    path('categories/add/', views.admin_category_add, name='category-add'),
    path('categories/edit/<int:pk>/', views.admin_category_edit, name='category-edit'),
    path('categories/delete/<int:pk>/', views.admin_category_delete, name='category-delete'),
]
