from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderDetail, Cart, CartDetail, Coupon, DeliveryFee, OrderAddress


# ====================================
# ORDER DETAIL INLINE
# ====================================

class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    readonly_fields = ['product', 'variant_color', 'variant_info', 'color_info', 'quantity', 'price', 'total']
    fields = ['product', 'variant_info', 'color_info', 'quantity', 'price', 'total']
    can_delete = False
    
    def variant_info(self, obj):
        """عرض معلومات النمط"""
        if obj.variant_color and obj.variant_color.variant:
            return format_html(
                '<strong>{}</strong><br><small>كود: {}</small>',
                obj.variant_color.variant.name,
                obj.variant_color.variant.code or '-'
            )
        return '-'
    variant_info.short_description = 'النمط'
    
    def color_info(self, obj):
        """عرض معلومات اللون"""
        if obj.variant_color and obj.variant_color.color:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<div style="width: 25px; height: 25px; background-color: {}; border: 1px solid #ddd; border-radius: 4px;"></div>'
                '<span>{}</span>'
                '</div>',
                obj.variant_color.color.hex_code or '#ccc',
                obj.variant_color.color.name
            )
        return '-'
    color_info.short_description = 'اللون'


# ====================================
# ORDER ADMIN
# ====================================

class OrderAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer_name', 'user', 'status_badge', 'total_display', 'order_time']
    list_filter = ['status', 'order_time']
    search_fields = ['code', 'user__email', 'address__customer_name', 'address__customer_phone']
    inlines = [OrderDetailInline]
    readonly_fields = ['code', 'order_time', 'total_display', 'customer_details']
    
    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('code', 'user', 'status', 'order_time')
        }),
        ('بيانات العميل', {
            'fields': ('customer_details',)
        }),
        ('المبالغ', {
            'fields': ('subtotal', 'delivery_fee', 'discount', 'total_display')
        }),
    )
    
    def customer_name(self, obj):
        """اسم العميل"""
        if obj.address:
            return obj.address.customer_name
        return '-'
    customer_name.short_description = 'العميل'
    customer_name.admin_order_field = 'address__customer_name'
    
    def status_badge(self, obj):
        """عرض حالة الطلب بألوان"""
        colors = {
            'Received': '#3498db',
            'Processed': '#f39c12',
            'Shipped': '#9b59b6',
            'Delivered': '#27ae60'
        }
        color = colors.get(obj.status, '#95a5a6')
        status_text = dict(Order._meta.get_field('status').choices).get(obj.status, obj.status)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 5px; font-weight: bold; display: inline-block;">{}</span>',
            color, status_text
        )
    status_badge.short_description = 'الحالة'
    
    def total_display(self, obj):
        """عرض الإجمالي"""
        return format_html(
            '<strong style="color: #27ae60; font-size: 16px;">{} جنيه</strong>',
            obj.total_with_coupon or obj.total or 0
        )
    total_display.short_description = 'الإجمالي'
    
    def customer_details(self, obj):
        """عرض تفاصيل العميل"""
        if not obj.address:
            return '-'
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">'
            '<p><strong>الاسم:</strong> {}</p>'
            '<p><strong>الهاتف:</strong> {}</p>'
            '<p><strong>البريد:</strong> {}</p>'
            '<p><strong>العنوان:</strong> {}</p>'
            '<p><strong>المحافظة:</strong> {}</p>'
            '{}'
            '</div>',
            obj.address.customer_name,
            obj.address.customer_phone,
            obj.address.customer_email or '-',
            obj.address.address_line,
            obj.address.governorate,
            f'<p><strong>ملاحظات:</strong> {obj.address.notes}</p>' if obj.address.notes else ''
        )
    customer_details.short_description = 'بيانات التوصيل'


# ====================================
# ORDER DETAIL ADMIN
# ====================================

class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'product_name', 'variant_name', 'color_preview', 'quantity', 'price_display', 'total_display']
    list_filter = ['order__status', 'order__order_time']
    search_fields = ['order__code', 'product__name']
    readonly_fields = ['order', 'product', 'variant_color', 'quantity', 'price', 'total']
    
    def order_code(self, obj):
        return obj.order.code
    order_code.short_description = 'رقم الطلب'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else '-'
    product_name.short_description = 'المنتج'
    
    def variant_name(self, obj):
        if obj.variant_color and obj.variant_color.variant:
            return obj.variant_color.variant.name
        return '-'
    variant_name.short_description = 'النمط'
    
    def color_preview(self, obj):
        if obj.variant_color and obj.variant_color.color:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<div style="width: 30px; height: 30px; background-color: {}; border: 2px solid #ddd; border-radius: 4px;"></div>'
                '<span>{}</span>'
                '</div>',
                obj.variant_color.color.hex_code or '#ccc',
                obj.variant_color.color.name
            )
        return '-'
    color_preview.short_description = 'اللown'
    
    def price_display(self, obj):
        return f'{obj.price} جنيه'
    price_display.short_description = 'السعر'
    
    def total_display(self, obj):
        return format_html(
            '<strong>{} جنيه</strong>',
            obj.total
        )
    total_display.short_description = 'الإجمالي'


# ====================================
# CART DETAIL INLINE
# ====================================

class CartDetailInline(admin.TabularInline):
    model = CartDetail
    extra = 0
    readonly_fields = ['product', 'variant_info', 'color_info', 'quantity', 'price_display']
    fields = ['product', 'variant_info', 'color_info', 'quantity', 'price_display']
    
    def variant_info(self, obj):
        if obj.variant_color and obj.variant_color.variant:
            return obj.variant_color.variant.name
        return '-'
    variant_info.short_description = 'النمط'
    
    def color_info(self, obj):
        if obj.variant_color and obj.variant_color.color:
            return format_html(
                '<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border: 1px solid #ddd; border-radius: 3px; margin-right: 5px;"></span>{}',
                obj.variant_color.color.hex_code or '#ccc',
                obj.variant_color.color.name
            )
        return '-'
    color_info.short_description = 'اللون'
    
    def price_display(self, obj):
        if obj.variant_color:
            return f'{obj.variant_color.price} جنيه'
        return '-'
    price_display.short_description = 'السعر'


# ====================================
# CART ADMIN
# ====================================

class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'items_count', 'total_display']
    list_filter = ['status']
    search_fields = ['user__email']
    inlines = [CartDetailInline]
    
    def items_count(self, obj):
        return obj.cart_detail.count()
    items_count.short_description = 'عدد المنتجات'
    
    def total_display(self, obj):
        return format_html(
            '<strong>{} جنيه</strong>',
            obj.cart_total
        )
    total_display.short_description = 'الإجمالي'


# ====================================
# REGISTER MODELS
# ====================================

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetail, OrderDetailAdmin)
admin.site.register(OrderAddress)
admin.site.register(Cart, CartAdmin)
admin.site.register(Coupon)
admin.site.register(DeliveryFee)