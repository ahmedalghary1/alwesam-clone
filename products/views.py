from django.views.generic import ListView,DetailView
from .models import Product,ProductImages

from django.db.models import Q




class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'object_list'
    paginate_by = 12  # عدد المنتجات في كل صفحة

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)  # Only show active products
        
        # Search in name, subtitle, and description
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(subtitle__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__name__icontains=search_query)  # Search in tags too
            )
        
        # Filter by category
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by brand
        brand = self.request.GET.get('brand', '')
        if brand:
            queryset = queryset.filter(brand__iexact=brand)
        
        # Filter by price range
        price_range = self.request.GET.get('price_range', '')
        if price_range:
            if price_range == '0-1000':
                queryset = queryset.filter(price__lt=1000)
            elif price_range == '1000-5000':
                queryset = queryset.filter(price__gte=1000, price__lt=5000)
            elif price_range == '5000-10000':
                queryset = queryset.filter(price__gte=5000, price__lt=10000)
            elif price_range == '10000-plus':
                queryset = queryset.filter(price__gte=10000)
        
        # Filter by availability
        availability = self.request.GET.get('availability', '')
        if availability == 'in_stock':
            queryset = queryset.filter(quantity__gt=0)
        elif availability == 'out_of_stock':
            queryset = queryset.filter(quantity=0)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')  # Default sorting
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        from .models import Category
        context = super().get_context_data(**kwargs)
        
        # Add all categories for filter
        context['categories'] = Category.objects.all()
        
        # Add all unique brands for filter
        context['brands'] = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct().exclude(brand='')
        
        # Keep search query and filters
        context['search_query'] = self.request.GET.get('search', '')
        
        return context



class ProductDetail(DetailView):
    model=Product
    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context["images"] = ProductImages.objects.filter(product=self.get_object())
        context["products"] = Product.objects.filter(tags__in=self.get_object().tags.all()).distinct()[:10]
        return context
    
