from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max
from .models import Product, ProductVariant, Category

# ==========================================================
#              PRODUCT LIST VIEW (مع الفلاتر الجديدة)
# ==========================================================

class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'object_list'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True) \
            .prefetch_related('variants')  \
            .distinct()

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

        # --- Sorting ---------------------------
        sort_by = self.request.GET.get('sort', '')

        if sort_by == 'name_asc':
            queryset = queryset.order_by('name')

        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')

        elif sort_by == 'newest':
            queryset = queryset.order_by('-id')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.all()
        context['brands'] = Product.objects.filter(is_active=True) \
            .values_list('brand', flat=True).distinct().exclude(brand='')

        context['search_query'] = self.request.GET.get('search', '')

        return context


class ProductDetail(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product = self.object

        # ---- جلب الأنماط مع الألوان والصور ----
        variants = ProductVariant.objects.filter(product=product).prefetch_related(
            'colors__color',  # جلب الألوان
            'images__color'   # جلب الصور
        )

        # تجهيز البيانات لإرسالها كـ JSON للقالب
        variants_data = []

        for variant in variants:
            # جلب جميع الألوان الخاصة بهذا النمط
            colors_list = []
            for variant_color in variant.colors.all():
                colors_list.append({
                    "id": variant_color.id,
                    "variant_color_id": variant_color.id,
                    "color_id": variant_color.color.id,
                    "name": variant_color.color.name,
                    "hex": variant_color.color.hex_code or "",
                    "price": variant_color.price,
                    "quantity": variant_color.quantity,
                    "sku": variant_color.sku or "",
                })

            # جلب جميع الصور الخاصة بهذا النمط
            images_list = []
            for img in variant.images.all():
                images_list.append({
                    "url": img.image.url,
                    "color_id": img.color.id if img.color else None
                })

            variants_data.append({
                "id": variant.id,
                "name": variant.name,
                "code": variant.code or "",
                "colors": colors_list,
                "images": images_list,
            })

        # ---- إضافة البيانات للكونتكس ----
        context["variants"] = variants
        context["variants_json"] = variants_data
        context["products"] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]

        return context
