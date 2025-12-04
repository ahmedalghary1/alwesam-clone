from django.contrib import admin
from .models import Product, ProductImages, Review, Category, ProductColor, Color


# --- Inline for Product Images ---
class ProductImagesInline(admin.TabularInline):
    model = ProductImages
    extra = 1


# --- Inline for Product Colors ---
class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ('color', 'price', 'quantity', 'code', 'mark')


# --- Product Admin ---
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImagesInline, ProductColorInline]
    list_filter = ('category', 'is_featured', 'is_active')


# --- Category Admin ---
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# --- Register Models ---
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Review)
admin.site.register(Color)
