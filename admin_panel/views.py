from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Min
from django.utils import timezone

from .decorators import admin_required
from .forms import ProductForm, OrderStatusForm, CategoryForm, ProductVariantFormSet, VariantImageFormSet
from products.models import Product, Category ,ProductVariant , ProductVariantImage
from orders.models import Order, OrderDetail
from accounts.models import CustomUser
from .forms import ProductVariantFormSet

@admin_required
def admin_dashboard(request):

    total_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Received').count()
    total_users = CustomUser.objects.count()

    recent_orders = Order.objects.all().order_by('-order_time')[:10]

    # 🔵 عرض المنتجات التي لها كميات منخفضة
    low_stock_products = (
        Product.objects
        .filter(variants__quantity__lt=10)
        .distinct()
        .order_by('variants__quantity')[:5]
    )

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
    # قاعدة: جلب كل المنتجات (يمكن تضيف .filter(is_active=True) لو أردت)
    products_qs = Product.objects.all().order_by("-id")

    # Search
    search = request.GET.get("search", "")
    if search:
        products_qs = products_qs.filter(name__icontains=search)

    # Filter by category
    category_id = request.GET.get("category", "")
    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    # Filter by status
    status = request.GET.get("status", "")
    if status == "active":
        products_qs = products_qs.filter(is_active=True)
    elif status == "inactive":
        products_qs = products_qs.filter(is_active=False)

    # Annotate: مجموع الكمية (sum of variant.quantity) وأقل سعر (min of variant.price)
    # استخدم distinct() فقط إذا أردت تجنّب مكررات عند وجود علاقات متعددة، لكن هنا annotate على علاقة FK يكفي
    products = products_qs.annotate(
        total_quantity=Sum('variants__quantity'),
        min_price=Min('variants__price'),
    )

    categories = Category.objects.all()

    context = {
        "products": products,
        "categories": categories,
        "search": search,
    }

    return render(request, "admin_panel/products_list.html", context)


@admin_required
def admin_product_create(request):

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        variant_formset = ProductVariantFormSet(request.POST, request.FILES)

        if form.is_valid() and variant_formset.is_valid():

            # 1) حفظ المنتج
            product = form.save()

            # 2) احفظ المتغيرات
            variants = variant_formset.save(commit=False)

            for index, variant in enumerate(variants):
                variant.product = product
                variant.save()

                # -----------------------------
                # 🔥 حفظ صور المتغير بدون formset
                # -----------------------------
                images = request.FILES.getlist(f"variant_{index}_images")

                for img in images:
                    ProductVariantImage.objects.create(
                        variant=variant,
                        image=img
                    )

            return redirect('admin_panel:products-list')

    else:
        form = ProductForm()
        variant_formset = ProductVariantFormSet()

    # لا نستخدم image_formsets لأننا لا نحتاجها في هذا النظام
    context = {
        'form': form,
        'variant_formset': variant_formset,
    }
    return render(request, 'admin_panel/product_form.html', context)

@admin_required
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        # لا تعيّن prefix إلا إذا كنت تستخدم نفس الـ prefix في القالب/JS
        variant_formset = ProductVariantFormSet(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid() and variant_formset.is_valid():
            # حفظ بيانات المنتج
            product = form.save()

            saved_variants = []

            # معالجة كل نموذج داخل الـ formset واحداً-واحد
            for i, vform in enumerate(variant_formset.forms):
                # إذا النموذج معلم للحذف وحالته موجودة في DB -> احذف
                if vform.cleaned_data.get('DELETE') and vform.instance.pk:
                    vform.instance.delete()
                    continue

                # حفظ المتغير (لم يتم ربطه بعد بالمنتج)
                variant = vform.save(commit=False)
                variant.product = product
                variant.save()
                saved_variants.append(variant)

                # الآن نحاول إيجاد أي ملفات صور أُرسلت لهذا الـ form
                # نجرّب عدة مفاتيح لأن الـ template أو JS قد يستخدم أحدها:
                # 1) vform.prefix + '_images'  (مثال: productvariant_set-0_images أو variants-0_images)
                # 2) 'variant_{index}_images' (مثال: variant_0_images) — حسب JS الذي يعيد الفهرسة
                # 3) fallback بسيط: نفس index في حالة عدم وجود prefix متوقع
                tried_keys = []
                keys_to_try = []

                # 1) prefix-based
                if hasattr(vform, 'prefix'):
                    keys_to_try.append(f"{vform.prefix}_images")

                # 2) index-based from prefix (أحياناً prefix يكون like 'form-0')
                if hasattr(vform, 'prefix'):
                    # خذ آخر رقم بعد '-'
                    parts = vform.prefix.split('-')
                    if parts:
                        idx_part = parts[-1]
                        if idx_part.isdigit():
                            keys_to_try.append(f"variant_{idx_part}_images")

                # 3) direct index i (forloop index fallback)
                keys_to_try.append(f"variant_{i}_images")

                # تخلّص التكرارات
                keys_to_try = [k for k in dict.fromkeys(keys_to_try) if k]

                # اجلب الملفات إذا وجدت تحت أي اسم من الأسماء
                for key in keys_to_try:
                    tried_keys.append(key)
                    images = request.FILES.getlist(key)
                    if images:
                        for img in images:
                            ProductVariantImage.objects.create(variant=variant, image=img)
                        # إذا وجدت صوراً تحت هذا المفتاح فلا نبحث في المفاتيح الأخرى
                        break

            # بعد حفظ/حذف المتغيرات، أخيراً استخدم save() للـ formset لإتمام حالات m2m إن وُجدت
            variant_formset.save()

            messages.success(request, "تم تحديث المنتج بنجاح.")
            return redirect("admin_panel:products-list")

        else:
            # أخطاء في الفورم أو الفورمسِت: اختياري إرسال رسالة خطأ
            messages.error(request, "هناك أخطاء في النموذج، رجاءً راجع البيانات.")

    else:
        form = ProductForm(instance=product)
        variant_formset = ProductVariantFormSet(instance=product)

    return render(request, "admin_panel/product_form.html", {
        "form": form,
        "variant_formset": variant_formset,
        "product": product,
        "action": "edit",
    })

@admin_required
def admin_product_delete(request, product_id):

    product = get_object_or_404(Product, id=product_id)
    name = product.name

    # حذف صور المتغيرات أولاً (احتياطي)
    for variant in product.variants.all():
        for img in variant.images.all():
            img.image.delete()  # حذف من media
            img.delete()

    # حذف المنتج وكل المتغيرات التابعة له
    product.delete()

    messages.success(request, f"تم حذف المنتج {name} بنجاح.")
    return redirect("admin_panel:products-list")

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
            category = form.save(commit=False)
            category.name = form.cleaned_data['name_ar']
            category.save()
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

