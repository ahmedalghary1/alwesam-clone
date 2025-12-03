from django import forms
from products.models import Product, ProductImages, Category, ProductColor
from orders.models import Order


class ProductForm(forms.ModelForm):
    """
    Form for creating/editing products.
    """
    class Meta:
        model = Product
        fields = [
            'name_ar', 'name_en','image',
            'subtitle_ar', 'subtitle_en',
            'description_ar', 'description_en',
            'category',  'brand',  'is_featured', 'is_active'
        ]
        widgets = {
            'name_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المنتج بالعربية'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المنتج بالإنجليزية'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'subtitle_ar': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف قصير (عربي)', 'rows': 3}),
            'subtitle_en': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Short Subtitle (English)', 'rows': 3}),
            
            'description_ar': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'الوصف الكامل (عربي)', 'rows': 6}),
            'description_en': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Full Description (English)', 'rows': 6}),
            
            'category': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العلامة التجارية (اختياري)'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductImageForm(forms.ModelForm):
    """
    Form for product additional images.
    """
    class Meta:
        model = ProductImages
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


# FormSet for managing multiple product images
ProductImageFormSet = forms.inlineformset_factory(
    Product,
    ProductImages,
    form=ProductImageForm,
    extra=1,
    can_delete=True
)


class ProductColorForm(forms.ModelForm):
    class Meta:
        model = ProductColor
        fields = ['color', 'price', 'quantity', 'code', 'mark']
        widgets = {
            'color': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'mark': forms.TextInput(attrs={'class': 'form-control'}),
        }


# FormSet for product colors
ProductColorFormSet = forms.inlineformset_factory(
    Product,
    ProductColor,
    form=ProductColorForm,
    extra=1,
    can_delete=True
)


class OrderStatusForm(forms.ModelForm):
    """
    Form for updating order status and delivery time.
    """
    class Meta:
        model = Order
        fields = ['status', 'delivery_time']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'delivery_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name_ar', 'name_en', 'description', 'icon']
        widgets = {
            'name_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الفئة بالعربية'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الفئة بالإنجليزية'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف الفئة', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-icon-name (اختياري)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name_ar = cleaned_data.get("name_ar")
        name_en = cleaned_data.get("name_en")

        # تجاهل نفس العنصر عند التعديل
        qs = Category.objects.all()
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if name_ar and qs.filter(name_ar__iexact=name_ar).exists():
            self.add_error("name_ar", "⚠️ هذه الفئة موجودة بالفعل باللغة العربية.")

        if name_en and qs.filter(name_en__iexact=name_en).exists():
            self.add_error("name_en", "⚠️ هذه الفئة موجودة بالفعل باللغة الإنجليزية.")

        return cleaned_data