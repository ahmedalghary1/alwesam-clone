from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    Category, Color, Product,
    ProductVariant, ProductVariantImage,
    Review
)


# ---------------------------------------------------------
# 🔵 Inline: صور الـ Variant
# ---------------------------------------------------------
class ProductVariantImageInline(admin.TabularInline):
    model = ProductVariantImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f"""
                <a href="{obj.image.url}" target="_blank">
                    <img src="{obj.image.url}" width="80" style="border-radius:6px;" />
                </a>
                """
            )
        return "No Image"

    image_preview.short_description = "Image"


# ---------------------------------------------------------
# 🔵 Inline: الـ Variants الخاصة بالمنتج (عرض كل الصور)
# ---------------------------------------------------------
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    show_change_link = True
    readonly_fields = ('variant_preview',)

    def variant_preview(self, obj):
        images = obj.images.all()
        if not images:
            return "No Images"

        html = ""
        for img in images:
            html += f"""
                <a href="{img.image.url}" target="_blank" style="margin-right:5px;">
                    <img src="{img.image.url}" width="80" style="border-radius:6px; margin:2px; border:1px solid #ddd;" />
                </a>
            """

        return mark_safe(html)

    variant_preview.short_description = "Variant Images"


# ---------------------------------------------------------
# 🔵 ModelAdmin: Categories
# ---------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    prepopulated_fields = {'slug': ('name',)}


# ---------------------------------------------------------
# 🔵 ModelAdmin: Colors
# ---------------------------------------------------------
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')
    search_fields = ('name',)


# ---------------------------------------------------------
# 🔵 ModelAdmin: Product
# ---------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'get_min_price', 'is_featured', 'is_active')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('name', 'brand', 'subtitle')
    inlines = [ProductVariantInline]

    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.main_image:
            return mark_safe(
                f"<a href='{obj.main_image.url}' target='_blank'>"
                f"<img src='{obj.main_image.url}' width='120' style='border-radius:6px;'/>"
                f"</a>"
            )
        return "No Image"

    image_preview.short_description = "Main Image"


# ---------------------------------------------------------
# 🔵 ModelAdmin: Variant (منفصل)
# ---------------------------------------------------------
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'price', 'quantity', 'color')
    list_filter = ('product', 'color')
    search_fields = ('name', 'product__name')
    inlines = [ProductVariantImageInline]


# ---------------------------------------------------------
# 🔵 ModelAdmin: Reviews
# ---------------------------------------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rate', 'created_at')
    list_filter = ('rate', 'created_at')
    search_fields = ('user__username', 'product__name', 'review')
