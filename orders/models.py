from django.db import models
from accounts.models import CustomUser 
from django.utils import timezone
import datetime

from products.models import Product, ProductVariant
from utils.generate_code import generate_code


ORDER_STATUS = (
    ('Received', 'تم الاستلام'),  
    ('Processed', 'قيد المعالجة'),
    ('Shipped', 'تم الشحن'),
    ('Delivered', 'تم التوصيل')
)


# ============================
#       Order Address
# ============================

class OrderAddress(models.Model):
    customer_name = models.CharField('اسم العميل', max_length=200)
    customer_phone = models.CharField('رقم الهاتف', max_length=15)
    customer_email = models.EmailField('البريد الإلكتروني', blank=True)
    governorate = models.CharField('المحافظة', max_length=100)
    city = models.CharField('المدينة', max_length=100, blank=True)
    address_line = models.TextField('العنوان بالتفصيل', max_length=500)
    notes = models.TextField('ملاحظات', blank=True, max_length=500)
    
    def __str__(self):
        return f"{self.customer_name} - {self.governorate}"


# ============================
#            Order
# ============================

class Order(models.Model):
    user = models.ForeignKey(CustomUser, related_name='order_owner',
                             on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(choices=ORDER_STATUS, max_length=20, default='Received')
    code = models.CharField(default=generate_code, max_length=20)
    order_time = models.DateTimeField(default=timezone.now)
    delivery_time = models.DateTimeField(blank=True, null=True)
    coupon = models.ForeignKey('Coupon', related_name='order_coupon',
                               on_delete=models.SET_NULL, blank=True, null=True)

    address = models.ForeignKey(OrderAddress, related_name='orders',
                                on_delete=models.SET_NULL, null=True, blank=True)

    subtotal = models.FloatField(default=0)
    delivery_fee = models.FloatField(default=0)
    discount = models.FloatField(default=0)
    total = models.FloatField(blank=True, null=True)
    total_with_coupon = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return f"Order #{self.code}"

    def calculate_total(self):
        subtotal = sum(detail.total for detail in self.order_detail.all())
        self.subtotal = subtotal
        
        self.total = subtotal + self.delivery_fee - self.discount

        if self.coupon:
            discount_value = (self.coupon.descount / 100) * self.total
            self.total_with_coupon = self.total - discount_value
        else:
            self.total_with_coupon = self.total
        
        return self.total_with_coupon

    class Meta:
        ordering = ['-order_time']


# ============================
#         Order Detail
# ============================

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, related_name='order_detail', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='orderdetail_product',
                                on_delete=models.SET_NULL, blank=True, null=True)

    # المهم: الآن الطلب يعتمد على ProductVariant
    variant = models.ForeignKey(ProductVariant, related_name='order_variant',
                                on_delete=models.SET_NULL, blank=True, null=True)

    quantity = models.IntegerField()
    price = models.FloatField()  # سعر قطعة الوحدة من الـ variant
    total = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.price = self.variant.price
        self.total = self.quantity * self.variant.price
        super().save(*args, **kwargs)


# ============================
#            Cart
# ============================

CART_STATUS = (
    ('Inprogress','Inprogress'),
    ('Completed','Completed'),
)


class Cart(models.Model):
    user = models.ForeignKey(CustomUser, related_name='cart_owner',
                             on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(choices=CART_STATUS, max_length=20)
    coupon = models.ForeignKey('Coupon', related_name='cart_coupon',
                               on_delete=models.SET_NULL, blank=True, null=True)

    total_with_coupon = models.FloatField(blank=True, null=True)

    @property
    def cart_total(self):
        return round(sum(item.total_price for item in self.cart_detail.all()), 2)


# ============================
#         Cart Detail
# ============================

class CartDetail(models.Model):
    cart = models.ForeignKey(Cart, related_name='cart_detail', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cartdetail_product',
                                on_delete=models.SET_NULL, blank=True, null=True)

    # المهم: هنا نستبدل ProductColor → ProductVariant
    variant = models.ForeignKey(ProductVariant, related_name="cart_variant",
                                on_delete=models.SET_NULL, blank=True, null=True)

    quantity = models.IntegerField(default=1)
    total = models.FloatField(blank=True, null=True)

    @property
    def price(self):
        return self.variant.price

    @property
    def total_price(self):
        return round(self.quantity * self.variant.price, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product.id,
            'product_name': self.product.name,
            'product_image': self.product.main_image.url if self.product.main_image else None,

            'variant_id': self.variant.id,
            'variant_name': self.variant.name,
            'variant_color': self.variant.color.name if self.variant.color else None,

            'quantity': self.quantity,
            'total': str(self.total_price),
            'product_price': str(self.variant.price),
        }


# ============================
#            Coupon
# ============================

class Coupon(models.Model):
    code = models.CharField(max_length=20)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True)
    quantity = models.IntegerField()
    descount = models.FloatField()

    def save(self, *args, **kwargs):
        if not self.end_date:
            week = datetime.timedelta(days=7)
            self.end_date = self.start_date + week

        super().save(*args, **kwargs)


# ============================
#       Delivery Fee
# ============================

class DeliveryFee(models.Model):
    fee = models.IntegerField()

    def __str__(self):
        return str(self.fee)
