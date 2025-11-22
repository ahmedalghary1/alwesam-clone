from django.core.management.base import BaseCommand
from orders.models import DeliveryFee


class Command(BaseCommand):
    help = 'إنشاء رسوم توصيل افتراضية'

    def handle(self, *args, **kwargs):
        # Check if delivery fee exists
        if DeliveryFee.objects.exists():
            self.stdout.write(self.style.WARNING('⚠️ رسوم التوصيل موجودة بالفعل'))
            return

        # Create default delivery fee
        delivery_fee = DeliveryFee.objects.create(
            fee=50.0,  # 50 جنيه رسوم توصيل افتراضية
        )

        self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء رسوم التوصيل: {delivery_fee.fee} جنيه'))
