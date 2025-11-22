from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from .decorators import admin_required
from .forms import ProductForm, ProductImageFormSet, OrderStatusForm, CategoryForm
from products.models import Product, Category
from orders.models import Order, OrderDetail
from accounts.models import CustomUser


@admin_required
def admin_dashboard(request):
    """
    Admin dashboard with statistics.
    """
    # Get statistics
    total_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Received').count()
    total_users = CustomUser.objects.count()
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-order_time')[:10]
    
    # Low stock products (quantity < 10)
    low_stock_products = Product.objects.filter(quantity__lt=10, is_active=True).order_by('quantity')[:5]
    
    # Revenue this month
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_revenue = Order.objects.filter(
        order_time__month=current_month,
        order_time__year=current_year
    ).aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_users': total_users,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'monthly_revenue': monthly_revenue,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_products_list(request):
    """
    List all products with search and filter.
    """
    products = Product.objects.all().order_by('-created_at')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        products = products.filter(name__icontains=search)
    
    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
    }
    
    return render(request, 'admin_panel/products_list.html', context)


@admin_required
def admin_product_create(request):
    """
    Create new product.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = ProductImageFormSet(request.POST, request.FILES)
        
        if form.is_valid():
            product = form.save()
            
            # Save additional images if formset is valid
            if formset.is_valid():
                formset.instance = product
                formset.save()
            
            messages.success(request, f'✅ تم إضافة المنتج "{product.name}" بنجاح.')
            return redirect('admin_panel:products-list')
    else:
        form = ProductForm()
        formset = ProductImageFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'action': 'create',
    }
    
    return render(request, 'admin_panel/product_form.html', context)


@admin_required
def admin_product_edit(request, product_id):
    """
    Edit existing product.
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid():
            product = form.save()
            
            if formset.is_valid():
                formset.save()
            
            messages.success(request, f'✅ تم تحديث المنتج "{product.name}" بنجاح.')
            return redirect('admin_panel:products-list')
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)
    
    context = {
        'form': form,
        'formset': formset,
        'product': product,
        'action': 'edit',
    }
    
    return render(request, 'admin_panel/product_form.html', context)


@admin_required
def admin_product_delete(request, product_id):
    """
    Delete product.
    """
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, f'✅ تم حذف المنتج "{product_name}" بنجاح.')
    return redirect('admin_panel:products-list')


@admin_required
def admin_orders_list(request):
    """
    List all orders with filters.
    """
    orders = Order.objects.all().order_by('-order_time')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    
    # Search by code or customer name
    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(code__icontains=search) | orders.filter(address__customer_name__icontains=search)
    
    context = {
        'orders': orders,
        'search': search,
        'selected_status': status,
    }
    
    return render(request, 'admin_panel/orders_list.html', context)


@admin_required
def admin_order_detail(request, order_code):
    """
    View and edit order details.
    """
    order = get_object_or_404(Order, code=order_code)
    order_details = OrderDetail.objects.filter(order=order)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ تم تحديث حالة الطلب #{order.code} بنجاح.')
            return redirect('admin_panel:order-detail', order_code=order_code)
    else:
        form = OrderStatusForm(instance=order)
    
    context = {
        'order': order,
        'order_details': order_details,
        'form': form,
    }
    
    return render(request, 'admin_panel/order_detail.html', context)


@admin_required
def admin_users_list(request):
    """
    List all users.
    """
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(email__icontains=search) | users.filter(first_name__icontains=search)
    
    context = {
        'users': users,
        'search': search,
    }
    
    return render(request, 'admin_panel/users_list.html', context)


# ==================== Categories Management ====================

@admin_required
def admin_categories_list(request):
    """
    List all categories with product count.
    """
    categories = Category.objects.annotate(
        products_count=Count('products')
    ).order_by('name')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)
    
    context = {
        'categories': categories,
        'search': search,
    }
    
    return render(request, 'admin_panel/categories_list.html', context)


@admin_required
def admin_category_add(request):
    """
    Add new category.
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'✅ تم إضافة الفئة "{category.name}" بنجاح.')
            return redirect('admin_panel:categories-list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'action': 'add',
    }
    
    return render(request, 'admin_panel/category_form.html', context)


@admin_required
def admin_category_edit(request, pk):
    """
    Edit existing category.
    """
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'✅ تم تحديث الفئة "{category.name}" بنجاح.')
            return redirect('admin_panel:categories-list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'action': 'edit',
    }
    
    return render(request, 'admin_panel/category_form.html', context)


@admin_required
def admin_category_delete(request, pk):
    """
    Delete category.
    """
    category = get_object_or_404(Category, pk=pk)
    category_name = category.name
    products_count = category.products.count()
    
    if products_count > 0:
        messages.warning(
            request, 
            f'⚠️ تحذير: الفئة "{category_name}" تحتوي على {products_count} منتج. سيتم إزالة الفئة من المنتجات فقط.'
        )
    
    category.delete()
    messages.success(request, f'✅ تم حذف الفئة "{category_name}" بنجاح.')
    return redirect('admin_panel:categories-list')

