import uuid
from django.db import models
from taggit.managers import TaggableManager
from accounts.models import CustomUser 
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    """
    Product categories for filtering and organization.
    """
    name = models.CharField('اسم الفئة', max_length=100)
    slug = models.SlugField(blank=True, null=True, unique=True)
    description = models.TextField('الوصف', max_length=500, blank=True)
    icon = models.CharField('أيقونة', max_length=50, blank=True, help_text='Font Awesome icon class')
    created_at = models.DateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

class Color(models.Model):
    name = models.CharField('name', max_length=50)
    hex_code = models.CharField(max_length=7, blank=True, null=True)   # مثل: #ff0000

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('name', max_length=120,blank=True,null=True)
    category = models.ForeignKey(Category, verbose_name='الفئة', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    subtitle = models.TextField('subtitle', max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='product_colors', blank=True, null=True)

    description = models.TextField('description', max_length=50000, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    tags = TaggableManager()
    brand = models.CharField('العلامة التجارية', max_length=100, blank=True)  # Optional brand field
    is_featured = models.BooleanField('مميز', default=False)  # Featured products
    is_active = models.BooleanField('نشط', default=True)  # Active/inactive products

    slug = models.SlugField(blank=True, null=True, unique=True)

    def get_default_color(self):
        return self.color.order_by('id').first()

    def get_min_price(self):
        color = self.color.order_by('price').first()
        return color.price if color else None
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
        
    def __str__(self) :
        return self.name

    class Meta :
        ordering = ['id']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'



class ProductColor(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='color',
        on_delete=models.CASCADE
    )
    color = models.ForeignKey(
        Color,
        related_name='product_colors',
        on_delete=models.CASCADE
    )
    price = models.FloatField()
    quantity = models.IntegerField()
    code = models.CharField(max_length=100)  # لكل لون كود خاص
    mark = models.CharField(max_length=100, blank=True, null=True)  # لو تريد علامة خاصة لكل لون

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"

class ProductImages(models.Model):
    product = models.ForeignKey(Product,verbose_name=('product'),related_name='product_image',on_delete=models.CASCADE)
    image = models.ImageField(('image'),upload_to='productimages')

class Review(models.Model):
    user = models.ForeignKey(CustomUser,related_name='review_user',on_delete=models.SET_NULL,null=True)
    product = models.ForeignKey(Product,related_name='Review_product',on_delete=models.CASCADE)
    review = models.TextField(('review'),max_length=500)
    rate = models.IntegerField(('rate'),choices=[(i,i) for i in range(1,6)])
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) :
        return f'{self.user}-{self.product}-{self.rate}'
    
