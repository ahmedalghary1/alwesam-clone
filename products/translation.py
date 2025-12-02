from modeltranslation.translator import register, TranslationOptions
from .models import Product , Category

@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description','subtitle')


@register(Category)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')
