from django import forms
from django.forms import inlineformset_factory

from products.models import (
    Product, Category,
    ProductVariant, ProductVariantImage, Color, VariantColor
)
from orders.models import Order


# ======================================================
# 🔵 Product Form
# ======================================================

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name_en','name_ar',
            'subtitle_ar','subtitle_en',
            'description_ar','description_en',
            'main_image',
            'category', 'brand',
            'is_featured', 'is_active'
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            
            'subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),

            'main_image': forms.FileInput(attrs={'class': 'form-control'}),

            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),

            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ======================================================
# 🔵 Variant Form
# ======================================================

class VariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'code']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ------------------------------------------------------
# Inline formset: Product -> Variants
# ------------------------------------------------------

ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=VariantForm,
    extra=1,
    can_delete=True
)


# ======================================================
# 🔵 Variant Image Form
# ======================================================

class VariantImageForm(forms.ModelForm):
    class Meta:
        model = ProductVariantImage
        fields = ['image', 'color']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'image': 'الصورة',
            'color': 'اللون (اختياري)',
        }


# ------------------------------------------------------
# Inline formset: Variant -> Images
# ------------------------------------------------------

VariantImageFormSet = inlineformset_factory(
    ProductVariant,
    ProductVariantImage,
    form=VariantImageForm,
    extra=1,
    can_delete=True
)


# ======================================================
# 🔵 Order Status Form
# ======================================================

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'delivery_time']

        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'delivery_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
        }


# ======================================================
# 🔵 Category Form
# ======================================================

class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = [
            'name_ar','name_en', 
            'description',
            'icon'
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-star مثلاً'}),
        }

    # 🔍 التحقق من تكرار اسم الفئة
    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name")

        qs = Category.objects.all()
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if name and qs.filter(name__iexact=name).exists():
            self.add_error("name", "⚠️ هذه الفئة موجودة بالفعل.")

        return cleaned


# ======================================================
# 🔵 Variant Color Form (لون النمط)
# ======================================================

class VariantColorForm(forms.ModelForm):
    class Meta:
        model = VariantColor
        fields = ['color', 'price', 'quantity', 'sku']
        
        widgets = {
            'color': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'السعر'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الكمية'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SKU (اختياري)'}),
        }


# ------------------------------------------------------
# Inline formset: Variant -> Colors
# ------------------------------------------------------

VariantColorFormSet = inlineformset_factory(
    ProductVariant,
    VariantColor,
    form=VariantColorForm,
    extra=1,
    can_delete=True
)
