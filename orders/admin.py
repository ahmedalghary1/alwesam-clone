from django.contrib import admin

from .models import Order, OrderDetail, Cart, CartDetail, Coupon, DeliveryFee, OrderAddress


class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'status', 'total', 'order_time')
    list_filter = ('status', 'order_time')
    search_fields = ('code', 'user__email', 'address__customer_name')
    inlines = [OrderDetailInline]

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetail)
admin.site.register(OrderAddress)
admin.site.register(Cart)
admin.site.register(CartDetail)
admin.site.register(Coupon)
admin.site.register(DeliveryFee)