from modeltranslation.translator import register, TranslationOptions
from .models import Product, Category, Color ,ProductVariant


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'subtitle')


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Color)
class ColorTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(ProductVariant)
class VariantranslationOptions(TranslationOptions):
    fields = ('name',)
