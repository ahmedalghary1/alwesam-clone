from modeltranslation.translator import register, TranslationOptions
from .models import Product , Category,Color

@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description','subtitle')


@register(Category)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Color)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name',)
