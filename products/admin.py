from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, 
    Color, 
    Product, 
    ProductVariant,
    VariantColor, 
    ProductVariantImage, 
    ProductReview
)


# ====================================
# CATEGORY ADMIN
# ====================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'created_at', 'product_count']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    def product_count(self, obj):
        count = obj.products.count()
        return format_html(
            '<span style="background-color: #fed72b; color: #292222; padding: 3px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            count
        )
    product_count.short_description = 'عدد المنتجات'

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ====================================
# COLOR ADMIN
# ====================================

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_preview', 'hex_code']
    search_fields = ['name', 'hex_code']
    
    def color_preview(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width: 50px; height: 25px; background-color: {}; border: 1px solid #ddd; border-radius: 5px;"></div>',
                obj.hex_code
            )
        return '-'
    color_preview.short_description = 'معاينة اللون'


# ====================================
# VARIANT IMAGE INLINE
# ====================================

class ProductVariantImageInline(admin.TabularInline):
    model = ProductVariantImage
    extra = 1
    fields = ['image', 'color', 'image_preview']
    readonly_fields = ['image_preview']
    verbose_name = 'صورة'
    verbose_name_plural = 'صور النمط'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 8px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'معاينة'


# ====================================
# VARIANT COLOR INLINE
# ====================================

class VariantColorInline(admin.TabularInline):
    model = VariantColor
    extra = 1
    fields = ['color', 'price', 'quantity', 'sku']
    verbose_name = 'لون النمط'
    verbose_name_plural = 'ألوان النمط'
    autocomplete_fields = ['color']


# ====================================
# PRODUCT VARIANT INLINE
# ====================================

class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    extra = 0
    fields = [
        'name', 
        'code',
    ]
    verbose_name = 'نمط المنتج'
    verbose_name_plural = 'أنماط المنتج (Variants)'


# ====================================
# PRODUCT VARIANT ADMIN
# ====================================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = [
        'get_product_name',
        'name',
        'code',
        'color_count',
        'image_count'
    ]
    list_filter = ['product__category', 'product__brand']
    search_fields = ['name', 'code', 'product__name']
    autocomplete_fields = ['product']
    inlines = [VariantColorInline, ProductVariantImageInline]
    
    fieldsets = (
        ('معلومات النمط', {
            'fields': ('product', 'name', 'code')
        }),
    )
    
    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = 'المنتج'
    get_product_name.admin_order_field = 'product__name'
    
    def color_count(self, obj):
        count = obj.colors.count()
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 10px; border-radius: 5px;">{} لون</span>',
            count
        )
    color_count.short_description = 'الألوان'
    
    def image_count(self, obj):
        count = obj.images.count()
        return format_html(
            '<span style="background-color: #9b59b6; color: white; padding: 3px 10px; border-radius: 5px;">{} صورة</span>',
            count
        )
    image_count.short_description = 'الصور'


# ====================================
# PRODUCT ADMIN
# ====================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview',
        'name',
        'category',
        'brand',
        'variant_count',
        'price_range',
        'stock_status',
        'is_featured',
        'is_active'
    ]
    list_filter = ['is_active', 'is_featured', 'category', 'brand']
    search_fields = ['name', 'subtitle', 'description', 'brand']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['category']
    readonly_fields = ['image_preview_large']
    inlines = [ProductVariantInline]
    
    list_editable = ['is_featured', 'is_active']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'slug', 'category', 'brand', 'subtitle')
        }),
        ('الصور', {
            'fields': ('main_image', 'image_preview_large')
        }),
        ('الوصف', {
            'fields': ('description',)
        }),
        ('الإعدادات', {
            'fields': ('is_featured', 'is_active')
        }),
    )
    
    def image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;" />',
                obj.main_image.url
            )
        return '-'
    image_preview.short_description = 'الصورة'
    
    def image_preview_large(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 12px;" />',
                obj.main_image.url
            )
        return '-'
    image_preview_large.short_description = 'معاينة الصورة'
    
    def variant_count(self, obj):
        count = obj.variants.count()
        return format_html(
            '<span style="background-color: #fed72b; color: #292222; padding: 3px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            count
        )
    variant_count.short_description = 'الأنماط'
    
    def price_range(self, obj):
        min_price = obj.get_min_price()
        
        if not min_price:
            return '-'
        
        # جمع كل الأسعار من جميع الألوان
        all_prices = []
        for variant in obj.variants.all():
            for vc in variant.colors.all():
                all_prices.append(vc.price)
        
        if not all_prices:
            return '-'
        
        min_p = min(all_prices)
        max_p = max(all_prices)
        
        if min_p == max_p:
            return format_html(
                '<span style="color: #fed72b; font-weight: bold;">{} جنيه</span>',
                min_p
            )
        else:
            return format_html(
                '<span style="color: #fed72b; font-weight: bold;">{} - {} جنيه</span>',
                min_p, max_p
            )
    price_range.short_description = 'نطاق السعر'
    
    def stock_status(self, obj):
        # استخدام دالة get_total_quantity من النموذج
        total_quantity = obj.get_total_quantity()
        
        if total_quantity > 50:
            color = '#27ae60'
            icon = '✓'
            text = 'متوفر'
        elif total_quantity > 0:
            color = '#f39c12'
            icon = '!'
            text = f'{total_quantity} فقط'
        else:
            color = '#e74c3c'
            icon = '✗'
            text = 'نفذ'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 5px; font-weight: bold;">{} {}</span>',
            color, icon, text
        )
    stock_status.short_description = 'حالة المخزون'


# ====================================

@admin.register(VariantColor)
class VariantColorAdmin(admin.ModelAdmin):
    list_display = ['get_product', 'get_variant', 'color', 'color_preview', 'price_display', 'quantity_display']
    list_filter = ['variant__product__category']
    search_fields = ['variant__name', 'color__name', 'variant__product__name']
    autocomplete_fields = ['variant', 'color']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('variant', 'color')
        }),
        ('السعر والمخزون', {
            'fields': ('price', 'quantity', 'sku')
        }),
    )
    
    def get_product(self, obj):
        return obj.variant.product.name
    get_product.short_description = 'المنتج'
    
    def get_variant(self, obj):
        return obj.variant.name
    get_variant.short_description = 'النمط'
    
    def color_preview(self, obj):
        if obj.color.hex_code:
            return format_html(
                '<div style="width: 40px; height: 25px; background-color: {}; border: 1px solid #ddd; border-radius: 5px;"></div>',
                obj.color.hex_code
            )
        return '-'
    color_preview.short_description = 'معاينة'
    
    def price_display(self, obj):
        return format_html(
            '<span style="color: #fed72b; font-weight: bold;">{} جنيه</span>',
            obj.price
        )
    price_display.short_description = 'السعر'
    
    def quantity_display(self, obj):
        color = '#27ae60' if obj.quantity > 10 else ('#f39c12' if obj.quantity > 0 else '#e74c3c')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color, obj.quantity
        )
    quantity_display.short_description = 'الكمية'


# ====================================
# PRODUCT VARIANT IMAGE ADMIN
# ====================================

@admin.register(ProductVariantImage)
class ProductVariantImageAdmin(admin.ModelAdmin):
    list_display = ['get_product', 'get_variant', 'image_preview']
    list_filter = ['variant__product__category']
    search_fields = ['variant__name', 'variant__product__name']
    autocomplete_fields = ['variant']
    
    def get_product(self, obj):
        return obj.variant.product.name
    get_product.short_description = 'المنتج'
    
    def get_variant(self, obj):
        return obj.variant.name
    get_variant.short_description = 'النمط'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'الصورة'


# ====================================
# PRODUCT REVIEW ADMIN
# ====================================

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating_display', 'comment_preview', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'product__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    def rating_display(self, obj):
        stars = '⭐' * obj.rating
        return format_html(
            '<span style="font-size: 18px;">{}</span>',
            stars
        )
    rating_display.short_description = 'التقييم'
    
    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'
    comment_preview.short_description = 'التعليق'


# ====================================
# تخصيص عنوان لوحة التحكم
# ====================================

admin.site.site_header = "لوحة تحكم متجر الوسام"
admin.site.site_title = "متجر الوسام"
admin.site.index_title = "مرحباً بك في لوحة التحكم"