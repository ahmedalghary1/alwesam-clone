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


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('name', max_length=120)
    category = models.ForeignKey(Category, verbose_name='الفئة', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    price = models.FloatField('price')
    image = models.ImageField('image', upload_to='product')
    subtitle = models.TextField('subtitle', max_length=500)
    description = models.TextField('description', max_length=50000)
    created_at = models.DateTimeField(default=timezone.now)
    quantity = models.IntegerField('quantity')
    tags = TaggableManager()
    brand = models.CharField('العلامة التجارية', max_length=100, blank=True)  # Optional brand field
    is_featured = models.BooleanField('مميز', default=False)  # Featured products
    is_active = models.BooleanField('نشط', default=True)  # Active/inactive products

    slug = models.SlugField(blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        self.slug =slugify(self.name)
        super(Product,self).save(*args, **kwargs)
    
    def __str__(self) :
        return self.name

    class Meta :
        ordering = ['id']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


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
    
