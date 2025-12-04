from django.views.generic import ListView,DetailView
from .models import Product,ProductImages,ProductColor

from django.db.models import Q



class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'object_list'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).distinct()

        # Search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(subtitle__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            )

        # Category filter
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Brand filter
        brand = self.request.GET.get('brand', '')
        if brand:
            queryset = queryset.filter(brand__iexact=brand)

        # Price filter
        price_range = self.request.GET.get('price_range', '')
        if price_range == '0-1000':
            queryset = queryset.filter(color__price__lt=1000)
        elif price_range == '1000-5000':
            queryset = queryset.filter(color__price__gte=1000, color__price__lt=5000)
        elif price_range == '5000-10000':
            queryset = queryset.filter(color__price__gte=5000, color__price__lt=10000)
        elif price_range == '10000-plus':
            queryset = queryset.filter(color__price__gte=10000)

        # Availability
        availability = self.request.GET.get('availability', '')
        if availability == 'in_stock':
            queryset = queryset.filter(color__quantity__gt=0)
        elif availability == 'out_of_stock':
            queryset = queryset.filter(color__quantity=0)

        # Sorting
        sort_by = self.request.GET.get('sort', '')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('color__price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-color__price')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        from .models import Category
        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.all()
        context['brands'] = Product.objects.filter(is_active=True)\
            .values_list('brand', flat=True).distinct().exclude(brand='')

        # Keep search query
        context['search_query'] = self.request.GET.get('search', '')

        return context



class ProductDetail(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product = self.get_object()

        # صور المنتج
        context["images"] = ProductImages.objects.filter(product=product)

        # الألوان الخاصة بهذا المنتج (ProductColor)
        context["product_colors"] = ProductColor.objects.filter(
            product=product
        ).select_related("color")

        # منتجات مشابهة
        context["products"] = Product.objects.filter(
            tags__in=product.tags.all()
        ).distinct()[:10]

        return context
