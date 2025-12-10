from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Min, Q
from django.utils import timezone

from .decorators import admin_required
from .forms import (
    ProductForm, CategoryForm, OrderStatusForm,
    VariantForm, VariantColorFormSet, VariantImageFormSet
)

from products.models import Product, Category, ProductVariant, ProductVariantImage, Color, VariantColor
from orders.models import Order, OrderDetail
from accounts.models import CustomUser


# ============================================================
# 🔵 Dashboard
# ============================================================

@admin_required
def admin_dashboard(request):

    total_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Received').count()
    total_users = CustomUser.objects.count()

    recent_orders = Order.objects.all().order_by('-order_time')[:10]

    # 🔵 المنتجات قليلة المخزون
    from products.models import VariantColor
    low_stock_variants = (
        VariantColor.objects
        .filter(quantity__lt=10, quantity__gt=0)
        .select_related('variant__product', 'color')
        .order_by('quantity')[:5]
    )

    # تحويلها لقائمة مع المعلومات المطلوبة
    low_stock_products = []
    for vc in low_stock_variants:
        low_stock_products.append({
            'product': vc.variant.product,
            'variant': vc.variant,
            'color': vc.color,
            'quantity': vc.quantity,
            'price': vc.price
        })

    current_time = timezone.now()
    monthly_revenue = Order.objects.filter(
        order_time__month=current_time.month,
        order_time__year=current_time.year
    ).aggregate(total=Sum('total'))['total'] or 0

    return render(request, 'admin_panel/dashboard.html', {
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_users': total_users,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'monthly_revenue': monthly_revenue,
    })


# ============================================================
# 🔵 Product List + Search + Filter
# ============================================================

@admin_required
def admin_products_list(request):

    products_qs = Product.objects.all().order_by("-id")

    # Search
    search = request.GET.get("search", "")
    if search:
        products_qs = products_qs.filter(
            Q(name__icontains=search)
        )

    # Filter by category
    category_id = request.GET.get("category", "")
    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    # status
    status = request.GET.get("status", "")
    if status == "active":
        products_qs = products_qs.filter(is_active=True)
    elif status == "inactive":
        products_qs = products_qs.filter(is_active=False)

    products = products_qs

    categories = Category.objects.all()

    return render(request, "admin_panel/products_list.html", {
        "products": products,
        "categories": categories,
        "search": search,
    })


# ============================================================
# 🔵 Create Product (with variants + images)
# ============================================================

@admin_required
def admin_product_create(request):

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)
            
            # حفظ الصورة الرئيسية إذا تم رفعها
            if 'main_image' in request.FILES:
                product.main_image = request.FILES['main_image']
            
            product.save()
            
            messages.success(request, "تم إضافة المنتج بنجاح. يمكنك الآن إضافة الأنماط من Django Admin.")
            return redirect('admin_panel:products-list')
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")

    else:
        form = ProductForm()

    return render(request, "admin_panel/product_form.html", {
        "form": form,
        "action": "add",
    })


# ============================================================
# 🔵 Edit Product
# ============================================================

@admin_required
def admin_product_edit(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            product = form.save(commit=False)
            
            # حفظ الصورة الرئيسية الجديدة إذا تم رفعها
            if 'main_image' in request.FILES:
                product.main_image = request.FILES['main_image']
            
            product.save()
            form.save_m2m()  # حفظ العلاقات many-to-many إن وجدت
            
            messages.success(request, "تم تحديث المنتج بنجاح.")
            return redirect("admin_panel:products-list")
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")

    else:
        form = ProductForm(instance=product)

    return render(request, "admin_panel/product_form.html", {
        "product": product,
        "form": form,
        "action": "edit",
    })


# ============================================================
# 🔵 Delete Product
# ============================================================

@admin_required
def admin_product_delete(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    # حذف صور الفاريانت
    for variant in product.variants.all():
        for img in variant.images.all():
            img.image.delete()
            img.delete()

    product.delete()
    messages.success(request, "تم حذف المنتج بنجاح.")

    return redirect("admin_panel:products-list")


# ============================================================
# 🔵 Orders List
# ============================================================

@admin_required
def admin_orders_list(request):

    orders = Order.objects.all().order_by('-order_time')

    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)

    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            Q(code__icontains=search) |
            Q(address__customer_name__icontains=search)
        )

    return render(request, 'admin_panel/orders_list.html', {
        'orders': orders,
        'search': search,
        'selected_status': status,
    })


# ============================================================
# 🔵 Order Detail
# ============================================================

@admin_required
def admin_order_detail(request, order_code):

    order = get_object_or_404(Order, code=order_code)
    order_details = OrderDetail.objects.filter(order=order)

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث الطلب بنجاح.")
            return redirect('admin_panel:order-detail', order_code=order_code)

    else:
        form = OrderStatusForm(instance=order)

    return render(request, 'admin_panel/order_detail.html', {
        'order': order,
        'order_details': order_details,
        'form': form,
    })


# ============================================================
# 🔵 Users List
# ============================================================

@admin_required
def admin_users_list(request):

    users = CustomUser.objects.all().order_by('-date_joined')

    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search)
        )

    return render(request, 'admin_panel/users_list.html', {
        'users': users,
        'search': search,
    })


# ============================================================
# 🔵 Categories List
# ============================================================

@admin_required
def admin_categories_list(request):

    categories = Category.objects.annotate(
        products_count=Count('products')
    ).order_by('name_ar')

    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(
            Q(name_ar__icontains=search) |
            Q(name_en__icontains=search)
        )

    return render(request, 'admin_panel/categories_list.html', {
        'categories': categories,
        'search': search,
    })


# ============================================================
# 🔵 Add Category
# ============================================================

@admin_required
def admin_category_add(request):

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, "تم إنشاء الفئة بنجاح.")
            return redirect('admin_panel:categories-list')

    else:
        form = CategoryForm()

    return render(request, 'admin_panel/category_form.html', {
        'form': form,
        'action': 'add',
    })


# ============================================================
# 🔵 Edit Category
# ============================================================

@admin_required
def admin_category_edit(request, pk):

    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث الفئة بنجاح.")
            return redirect('admin_panel:categories-list')

    else:
        form = CategoryForm(instance=category)

    return render(request, 'admin_panel/category_form.html', {
        'form': form,
        'category': category,
        'action': 'edit',
    })


# ============================================================
# 🔵 Delete Category
# ============================================================

@admin_required
def admin_category_delete(request, pk):

    category = get_object_or_404(Category, pk=pk)
    name = category.name_ar

    if category.products.exists():
        messages.warning(request,
            f"⚠️ الفئة '{name}' تحتوي على منتجات، سيتم حذف الفئة وربط المنتجات بدون فئة."
        )

    category.delete()

    messages.success(request, "تم حذف الفئة بنجاح.")
    return redirect('admin_panel:categories-list')


# ============================================================
# 🔵 Product Variants List
# ============================================================

@admin_required
def admin_product_variants(request, product_id):
    """عرض قائمة أنماط المنتج"""
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all().prefetch_related('colors', 'images')
    
    return render(request, 'admin_panel/product_variants.html', {
        'product': product,
        'variants': variants,
    })


# ============================================================
# 🔵 Add Variant
# ============================================================

@admin_required
def admin_variant_add(request, product_id):
    """إضافة نمط جديد للمنتج"""
    product = get_object_or_404(Product, id=product_id)
    colors = Color.objects.all()
    
    if request.method == 'POST':
        form = VariantForm(request.POST)
        
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            
            # معالجة الألوان
            color_formset = VariantColorFormSet(request.POST, instance=variant, prefix='colors')
            image_formset = VariantImageFormSet(request.POST, request.FILES, instance=variant, prefix='images')
            
            if color_formset.is_valid():
                color_formset.save()
            
            if image_formset.is_valid():
                image_formset.save()
            
            messages.success(request, "تم إضافة النمط بنجاح.")
            return redirect('admin_panel:product-variants', product_id=product.id)
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
            color_formset = VariantColorFormSet(request.POST, prefix='colors')
            image_formset = VariantImageFormSet(request.POST, request.FILES, prefix='images')
    else:
        form = VariantForm()
        color_formset = VariantColorFormSet(prefix='colors')
        image_formset = VariantImageFormSet(prefix='images')
    
    return render(request, 'admin_panel/variant_form.html', {
        'product': product,
        'form': form,
        'color_formset': color_formset,
        'image_formset': image_formset,
        'colors': colors,
        'action': 'add',
    })


# ============================================================
# 🔵 Edit Variant
# ============================================================

@admin_required
def admin_variant_edit(request, variant_id):
    """تعديل نمط موجود"""
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product
    colors = Color.objects.all()
    
    if request.method == 'POST':
        form = VariantForm(request.POST, instance=variant)
        color_formset = VariantColorFormSet(request.POST, instance=variant, prefix='colors')
        image_formset = VariantImageFormSet(request.POST, request.FILES, instance=variant, prefix='images')
        
        if form.is_valid():
            form.save()
            
            if color_formset.is_valid():
                color_formset.save()
            
            if image_formset.is_valid():
                image_formset.save()
            
            messages.success(request, "تم تحديث النمط بنجاح.")
            return redirect('admin_panel:product-variants', product_id=product.id)
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        form = VariantForm(instance=variant)
        color_formset = VariantColorFormSet(instance=variant, prefix='colors')
        image_formset = VariantImageFormSet(instance=variant, prefix='images')
    
    return render(request, 'admin_panel/variant_form.html', {
        'product': product,
        'variant': variant,
        'form': form,
        'color_formset': color_formset,
        'image_formset': image_formset,
        'colors': colors,
        'action': 'edit',
    })


# ============================================================
# 🔵 Delete Variant
# ============================================================

@admin_required
def admin_variant_delete(request, variant_id):
    """حذف نمط"""
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_id = variant.product.id
    variant_name = variant.name
    
    # حذف صور النمط
    for img in variant.images.all():
        if img.image:
            img.image.delete()
        img.delete()
    
    # حذف ألوان النمط
    variant.colors.all().delete()
    
    # حذف النمط
    variant.delete()
    
    messages.success(request, f"تم حذف النمط '{variant_name}' بنجاح.")
    return redirect('admin_panel:product-variants', product_id=product_id)
