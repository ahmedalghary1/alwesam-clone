
from django.db import models
from accounts.models import CustomUser 
from django.utils import timezone
import datetime


from products.models import Product
from utils.generate_code import generate_code



ORDER_STATUS = (
    ('Received', 'تم الاستلام'),  
    ('Processed', 'قيد المعالجة'),
    ('Shipped', 'تم الشحن'),
    ('Delivered', 'تم التوصيل')
)


class OrderAddress(models.Model):
    """
    Delivery address for orders.
    """
    customer_name = models.CharField('اسم العميل', max_length=200)
    customer_phone = models.CharField('رقم الهات ف', max_length=15)
    customer_email = models.EmailField('البريد الإلكتروني', blank=True)
    governorate = models.CharField('المحافظة', max_length=100)
    city = models.CharField('المدينة', max_length=100, blank=True)
    address_line = models.TextField('العنوان بالتفصيل', max_length=500)
    notes = models.TextField('ملاحظات', blank=True, max_length=500)
    
    def __str__(self):
        return f"{self.customer_name} - {self.governorate}"


class Order(models.Model):
    user = models.ForeignKey(CustomUser, related_name='order_owner', on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(choices=ORDER_STATUS, max_length=20, default='Received')
    code = models.CharField(default=generate_code, max_length=20)
    order_time = models.DateTimeField(default=timezone.now)
    delivery_time = models.DateTimeField(blank=True, null=True)  # Fixed spelling
    coupon = models.ForeignKey('Coupon', related_name='order_coupon', on_delete=models.SET_NULL, blank=True, null=True)
    
    # Customer information
    address = models.ForeignKey(OrderAddress, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Price fields
    subtotal = models.FloatField('المجموع الفرعي', default=0)
    delivery_fee = models.FloatField('رسوم التوصيل', default=0)
    discount = models.FloatField('الخصم', default=0)
    total = models.FloatField('الإجمالي', blank=True, null=True)
    total_with_coupon = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return f"Order #{self.code}"
    
    def calculate_total(self):
        """Calculate order total from order details."""
        subtotal = sum([detail.total for detail in self.order_detail.all()])
        self.subtotal = subtotal
        self.total = subtotal + self.delivery_fee - self.discount
        if self.coupon:
            discount = (self.coupon.descount / 100) * self.total
            self.total_with_coupon = self.total - discount
        else:
            self.total_with_coupon = self.total
        return self.total_with_coupon
    
    class Meta:
        ordering = ['-order_time']


class OrderDetail(models.Model):
    order = models.ForeignKey(Order,related_name = 'order_detail',on_delete = models.CASCADE)
    product = models.ForeignKey(Product,related_name = 'orderdetail_product',on_delete = models.SET_NULL,blank=True, null=True)
    quantity = models.IntegerField()
    price = models.FloatField()
    total = models.FloatField(blank=True, null=True)



CART_STATUS = (
    ('Inprogress','Inprogress'),
    ('Completed','Completed'),

)



class Cart(models.Model):
    user = models.ForeignKey(CustomUser,related_name='cart_owner',on_delete=models.SET_NULL,blank=True, null=True)
    status = models.CharField( choices=CART_STATUS,max_length=20)
    coupon = models.ForeignKey('Coupon',related_name='cart_coupon',on_delete=models.SET_NULL,blank=True, null=True)
    total_with_coupon = models.FloatField(blank=True, null=True)

    @property
    def cart_total(self):
        total = 0
        for item in self.cart_detail.all():
            total += item.total
        return round(total,2)

class CartDetail(models.Model):
    cart = models.ForeignKey(Cart,related_name = 'cart_detail',on_delete = models.CASCADE)
    product = models.ForeignKey(Product,related_name = 'cartdetail_product',on_delete = models.SET_NULL,blank=True, null=True)
    quantity = models.IntegerField(default=1)
    total = models.FloatField(blank=True, null=True)
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product.id,
            'product_name': self.product.name,
            'product_image': self.product.image.url if self.product.image else None ,  # If you have image URLs
            'quantity': self.quantity,
            'total': str(self.total),
            'product_price': str(self.product.price),
        }

class Coupon(models.Model):
    code = models.CharField(max_length=20)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True)
    quantity = models.IntegerField()
    descount = models.FloatField()
    def save(self, *args, **kwargs):
        if not self.end_date:
            week = datetime.timedelta(days=7) 
            self.end_date=self.start_date + week

        super(Coupon, self).save(*args, **kwargs) # Call the real save() method


class DeliveryFee(models.Model):
    fee = models.IntegerField()

    def __str__(self) :
        return str(self.fee)