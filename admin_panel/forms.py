from django import forms
from products.models import Product, ProductImages, Category
from orders.models import Order


class ProductForm(forms.ModelForm):
    """
    Form for creating/editing products.
    """
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'quantity', 'brand', 
                  'subtitle', 'description', 'image', 'is_featured', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المنتج'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'السعر', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الكمية المتوفرة'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العلامة التجارية (اختياري)'}),
            'subtitle': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف قصير', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'الوصف الكامل', 'rows': 6}),
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
    extra=1,  # عدد الحقول الفارغة الإضافية
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
    """
    Form for creating/editing categories.
    """
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الفئة'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف الفئة', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-icon-name (اختياري)'}),
        }
