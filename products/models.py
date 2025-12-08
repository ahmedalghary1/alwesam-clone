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
    """
    نموذج الألوان المتاحة في المتجر
    """
    name = models.CharField('اسم اللون', max_length=50)
    hex_code = models.CharField('كود اللون', max_length=7, blank=True, null=True, help_text='مثال: #ff0000')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'لون'
        verbose_name_plural = 'الألوان'
        ordering = ['name']


class Product(models.Model):
    """
    نموذج المنتج الأساسي
    """
    name = models.CharField('اسم المنتج', max_length=120, db_index=True)
    category = models.ForeignKey(
        Category, 
        related_name='products',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_index=True,
        verbose_name='الفئة'
    )
    subtitle = models.TextField('العنوان الفرعي', max_length=500, blank=True, null=True)
    main_image = models.ImageField('الصورة الرئيسية', upload_to='products', blank=True, null=True)
    description = models.TextField('الوصف', max_length=50000, blank=True, null=True)
    brand = models.CharField('العلامة التجارية', max_length=100, blank=True)
    is_featured = models.BooleanField('منتج مميز', default=False)
    is_active = models.BooleanField('نشط', default=True)
    slug = models.SlugField('الرابط', blank=True, null=True, unique=True)

    def __str__(self):
        return self.name

    def get_min_price(self):
        """الحصول على أقل سعر من جميع الأنماط والألوان"""
        min_price = None
        for variant in self.variants.all():
            variant_colors = variant.colors.all()
            if variant_colors:
                for vc in variant_colors:
                    if min_price is None or vc.price < min_price:
                        min_price = vc.price
        return min_price

    def get_total_quantity(self):
        """الحصول على إجمالي الكمية المتاحة"""
        total = 0
        for variant in self.variants.all():
            for vc in variant.colors.all():
                total += vc.quantity
        return total

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

    class Meta:
        ordering = ['id']
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'


class ProductVariant(models.Model):
    """
    نموذج نمط المنتج (مثال: 3 منافذ USB + 3 منافذ كهرباء)
    """
    product = models.ForeignKey(
        Product,
        related_name='variants',
        on_delete=models.CASCADE,
        verbose_name='المنتج'
    )
    name = models.CharField('اسم النمط', max_length=200, help_text='مثال: 3 USB + 3 منافذ')
    code = models.CharField('كود النمط', max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def get_min_price(self):
        """الحصول على أقل سعر من ألوان هذا النمط"""
        colors = self.colors.all()
        if not colors:
            return None
        return min(vc.price for vc in colors)

    def get_total_quantity(self):
        """الحصول على إجمالي الكمية من جميع الألوان"""
        return sum(vc.quantity for vc in self.colors.all())

    class Meta:
        verbose_name = 'نمط منتج'
        verbose_name_plural = 'أنماط المنتجات'
        ordering = ['id']


class VariantColor(models.Model):
    """
    نموذج لون النمط - يحتوي على السعر والكمية لكل لون في كل نمط
    """
    variant = models.ForeignKey(
        ProductVariant,
        related_name='colors',
        on_delete=models.CASCADE,
        verbose_name='النمط'
    )
    color = models.ForeignKey(
        Color,
        related_name='variant_colors',
        on_delete=models.CASCADE,
        verbose_name='اللون'
    )
    price = models.FloatField('السعر')
    quantity = models.IntegerField('الكمية', default=0)
    sku = models.CharField('SKU', max_length=50, blank=True, null=True, help_text='رمز تعريف المنتج')

    def __str__(self):
        return f"{self.variant.name} - {self.color.name}"

    class Meta:
        verbose_name = 'لون النمط'
        verbose_name_plural = 'ألوان الأنماط'
        unique_together = ('variant', 'color')
        ordering = ['variant', 'color']


class ProductVariantImage(models.Model):
    """
    صور النمط - يمكن ربطها بلون معين أو تكون عامة للنمط
    """
    variant = models.ForeignKey(
        ProductVariant,
        related_name='images',
        on_delete=models.CASCADE,
        verbose_name='النمط'
    )
    image = models.ImageField('الصورة', upload_to='variant_images')
    color = models.ForeignKey(
        Color,
        related_name='variant_images',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='اللون',
        help_text='اختياري - إذا كانت الصورة خاصة بلون معين'
    )

    def __str__(self):
        if self.color:
            return f"{self.variant.name} - {self.color.name}"
        return f"{self.variant.name} - صورة عامة"

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

    class Meta:
        verbose_name = 'صورة النمط'
        verbose_name_plural = 'صور الأنماط'


class Review(models.Model):
    """
    نموذج تقييمات المنتجات
    """
    user = models.ForeignKey(
        CustomUser,
        related_name='review_user',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='المستخدم'
    )
    product = models.ForeignKey(
        Product,
        related_name='Review_product',
        on_delete=models.CASCADE,
        verbose_name='المنتج'
    )
    review = models.TextField('التقييم', max_length=500)
    rate = models.IntegerField('التقدير', choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField('تاريخ الإنشاء', default=timezone.now)

    def __str__(self):
        return f'{self.user} - {self.product} - {self.rate}★'

    class Meta:
        verbose_name = 'تقييم'
        verbose_name_plural = 'التقييمات'
        ordering = ['-created_at']

