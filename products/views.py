from django.views.generic import ListView, DetailView
from django.db.models import Q, Min
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from django.contrib import messages

from .models import Product, ProductVariant, Category, ProductVariantImage, ProductReview
from orders.models import OrderDetail
import json


# ==========================================================
#              PRODUCT LIST VIEW (مع الفلاتر الجديدة)
# ==========================================================
# ==========================================================
#              PRODUCT LIST VIEW (مع الفلاتر الجديدة)
# ==========================================================
# ==========================================================
#              PRODUCT LIST VIEW (مع الفلاتر الجديدة)
# ==========================================================
class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'object_list'
    paginate_by = 12

    def get_queryset(self):
        # جلب المنتجات النشطة التي لديها أسعار
        queryset = Product.objects.filter(
            is_active=True,
            variants__colors__price__isnull=False
        ).annotate(
            min_price=Min('variants__colors__price')
        ).distinct()

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

        # --- Price Range Filter من القالب ---------------------
        price_range = self.request.GET.get('price_range', '')
        
        if price_range:
            if price_range == '0-1000':
                queryset = queryset.filter(min_price__lt=1000)
            elif price_range == '1000-5000':
                queryset = queryset.filter(min_price__gte=1000, min_price__lte=5000)
            elif price_range == '5000-10000':
                queryset = queryset.filter(min_price__gte=5000, min_price__lte=10000)
            elif price_range == '10000-plus':
                queryset = queryset.filter(min_price__gte=10000)

        # --- Sorting ---------------------------
        sort_by = self.request.GET.get('sort', '')
        if sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-id')
        elif sort_by == 'price_asc':
            queryset = queryset.order_by('min_price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-min_price')
        else:
            queryset = queryset.order_by('id')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        
        # تمرير قيم الفلترة للقالب لتحديد الخيارات المحددة
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_price_range'] = self.request.GET.get('price_range', '')
        context['selected_sort'] = self.request.GET.get('sort', '')
        
        # تمرير categories للقالب (يجب أن تكون موجودة بالفعل)
        
        return context
# ==========================================================
class ProductDetail(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product = self.object
        user = self.request.user

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
        context["variants_json"] = json.dumps(variants_data)
        context["images"] = variant.images.all() 

        context["products"] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]

        # ---- التقييمات ----
        reviews = ProductReview.objects.filter(product=product).select_related('user')
        context["reviews"] = reviews
        context["reviews_count"] = reviews.count()
        context["average_rating"] = product.get_average_rating()
        
        # ---- التحقق من إمكانية التقييم ----
        can_review = False
        has_reviewed = False
        user_review = None
        
        if user.is_authenticated:
            # التحقق من أن المستخدم اشترى المنتج وتم التسليم
            has_purchased = OrderDetail.objects.filter(
                order__user=user,
                product=product,
                order__status='Delivered'
            ).exists()
            
            # التحقق من أن المستخدم لم يقم بالتقييم من قبل
            user_review = ProductReview.objects.filter(product=product, user=user).first()
            has_reviewed = user_review is not None
            
            can_review = has_purchased and not has_reviewed
        
        context["can_review"] = can_review
        context["has_reviewed"] = has_reviewed
        context["user_review"] = user_review

        return context


# ==========================================================
#              REVIEW VIEWS (التقييمات)
# ==========================================================

@login_required
def add_review(request, slug):
    """
    إضافة تقييم جديد للمنتج (AJAX)
    """

    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        user = request.user
        
        # التحقق من أن المستخدم اشترى المنتج وتم التسليم
        has_purchased = OrderDetail.objects.filter(
            order__user=user,
            product=product,
            order__status='Delivered'
        ).exists()
        
        if not has_purchased:
            return JsonResponse({
                'success': False,
                'message': _('❌ يجب شراء المنتج أولاً لتتمكن من التقييم.')
            }, status=403)
        
        # التحقق من عدم وجود تقييم سابق
        if ProductReview.objects.filter(product=product, user=user).exists():
            return JsonResponse({
                'success': False,
                'message': _('❌ لقد قمت بتقييم هذا المنتج من قبل.')
            }, status=400)
        
        # الحصول على البيانات
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        
        # التحقق من التقييم
        if not rating or not rating.isdigit():
            return JsonResponse({
                'success': False,
                'message': _('❌ يرجى اختيار عدد النجوم.')
            }, status=400)
        
        rating = int(rating)
        if rating < 1 or rating > 5:
            return JsonResponse({
                'success': False,
                'message': _('❌ التقييم يجب أن يكون من 1 إلى 5 نجوم.')
            }, status=400)
        
        # إنشاء التقييم
        review = ProductReview.objects.create(
            product=product,
            user=user,
            rating=rating,
            comment=comment
        )
        
        return JsonResponse({
            'success': True,
            'message': _('✅ شكراً لك! تم إضافة تقييمك بنجاح.'),
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'user_name': user.first_name or user.email.split('@')[0],
                'created_at': review.created_at.strftime('%Y-%m-%d'),
            },
            'new_average': product.get_average_rating(),
            'new_count': product.get_reviews_count()
        })


@login_required
def delete_review(request, review_id):
    """
    حذف تقييم المستخدم
    """
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    product = review.product
    review.delete()
    
    return JsonResponse({
        'success': True,
        'message': _('✅ تم حذف التقييم بنجاح.'),
        'new_average': product.get_average_rating(),
        'new_count': product.get_reviews_count()
    })
