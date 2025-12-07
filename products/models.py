import uuid
from django.db import models
from taggit.managers import TaggableManager
from accounts.models import CustomUser 
from django.utils import timezone
from django.utils.text import slugify

from utils.compriss_image import convert_to_webp_and_delete_original

class Category(models.Model):
    """
    Product categories for filtering and organization.
    """
    name = models.CharField('اسم الفئة', max_length=100 , db_index=True)
    slug = models.SlugField(blank=True, null=True, unique=True, db_index=True)
    description = models.TextField('الوصف', max_length=500, blank=True)
    icon = models.CharField('أيقونة', max_length=50, blank=True, help_text='Font Awesome icon class')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1

            # لو الـ slug موجود، أضف -1, -2, -3 إلخ...
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

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
    name = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    category = models.ForeignKey(
        Category, related_name='products',
        on_delete=models.SET_NULL, null=True, blank=True, db_index=True
    )
    subtitle = models.TextField(max_length=500, blank=True, null=True)
    main_image = models.ImageField(upload_to='products', blank=True, null=True)
    description = models.TextField(max_length=50000, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(blank=True, null=True, unique=True)

    def __str__(self):
        return self.name

    def get_default_color(self):
        first_variant = self.variants.order_by('id').first()
        return first_variant.color if first_variant else None

    def get_min_price(self):
        first_variant = self.variants.order_by('price').first()
        return first_variant.price if first_variant else None

    def save(self, *args, **kwargs):
        is_new_image = False

        if self.main_image:  
            if self.pk:
                old = Product.objects.filter(pk=self.pk).first()
                if old and old.main_image.name != self.main_image.name:
                    is_new_image = True
            else:
                is_new_image = True

        super().save(*args, **kwargs)

        # معالجة الصورة إن كانت جديدة
        if self.main_image and is_new_image:
            convert_to_webp_and_delete_original(self.main_image)
            super().save(update_fields=['main_image'])

        # إنشاء slug إذا لم يوجد
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            super().save(update_fields=['slug'])
    def __str__(self) :
        return self.name

    class Meta :
        ordering = ['id']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='variants',
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=200)  # مثال: "3 USB + 3 منافذ"
    price = models.FloatField()
    quantity = models.IntegerField(default=0)
    code = models.CharField(max_length=50, blank=True, null=True)  # رقم خاص لكل نمط

    # لو كنت تحتاج لون أيضاً
    color = models.ForeignKey(
        Color, related_name="variant_colors",
        on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.product.name} - {self.name}"




class ProductVariantImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='variant_images')

    def __str__(self):
        return f"{self.variant.name} Image"

    def save(self, *args, **kwargs):
        is_new_image = False

        if self.image:
            if self.pk:
                old = ProductVariantImage.objects.filter(pk=self.pk).first()
                if old and old.image.name != self.image.name:
                    is_new_image = True
            else:
                is_new_image = True

        super().save(*args, **kwargs)

        if self.image and is_new_image:
            convert_to_webp_and_delete_original(self.image)
            super().save(update_fields=['image'])


class Review(models.Model):
    user = models.ForeignKey(CustomUser,related_name='review_user',on_delete=models.SET_NULL,null=True)
    product = models.ForeignKey(Product,related_name='Review_product',on_delete=models.CASCADE)
    review = models.TextField(('review'),max_length=500)
    rate = models.IntegerField(('rate'),choices=[(i,i) for i in range(1,6)])
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) :
        return f'{self.user}-{self.product}-{self.rate}'
    
