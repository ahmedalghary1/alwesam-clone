from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max
from .models import Product, ProductVariant, ProductVariantImage, Category


# ==========================================================
#              PRODUCT LIST VIEW (مع الفلاتر الجديدة)
# ==========================================================

class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'object_list'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).distinct()

        # --- Search ---------------------------
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(subtitle__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # --- Category Filter ------------------
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # --- Brand Filter ---------------------
        brand = self.request.GET.get('brand', '')
        if brand:
            queryset = queryset.filter(brand__iexact=brand)

        # --- Price Filter (Now uses ProductVariant) ----
        price_range = self.request.GET.get('price_range', '')

        if price_range == '0-1000':
            queryset = queryset.filter(variants__price__lt=1000)

        elif price_range == '1000-5000':
            queryset = queryset.filter(
                variants__price__gte=1000,
                variants__price__lt=5000
            )

        elif price_range == '5000-10000':
            queryset = queryset.filter(
                variants__price__gte=5000,
                variants__price__lt=10000
            )

        elif price_range == '10000-plus':
            queryset = queryset.filter(variants__price__gte=10000)

        # --- Availability Filter ---------------
        availability = self.request.GET.get('availability', '')
        if availability == 'in_stock':
            queryset = queryset.filter(variants__quantity__gt=0)

        elif availability == 'out_of_stock':
            queryset = queryset.filter(variants__quantity=0)

        # --- Sorting ---------------------------
        sort_by = self.request.GET.get('sort', '')

        if sort_by == 'price_asc':
            queryset = queryset.order_by('variants__price')

        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-variants__price')

        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')

        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')

        elif sort_by == 'newest':
            queryset = queryset.order_by('-id')

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.all()

        # All unique brands
        context['brands'] = Product.objects.filter(is_active=True) \
            .values_list('brand', flat=True).distinct().exclude(brand='')

        context['search_query'] = self.request.GET.get('search', '')

        return context



# ==========================================================
#              PRODUCT DETAIL VIEW (معلومات المنتج)
# ==========================================================

class ProductDetail(DetailView):
    model = Product
    template_name = "product_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        # --- صور المنتج: من أول Variant
        first_variant = product.variants.first()
        if first_variant:
            context["images"] = ProductVariantImage.objects.filter(
                variant=first_variant
            )
        else:
            context["images"] = []

        # --- جميع المتغيرات (الألوان – الأسعار – الكميات)
        context["variants"] = product.variants.select_related("color")

        # --- منتجات مشابهة (حسب الاسم أو الوصف)
        context["products"] = Product.objects.filter(
            Q(category=product.category) |
            Q(brand=product.brand)
        ).exclude(id=product.id).distinct()[:10]

        return context
