from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = 'إنشاء تصنيفات تجريبية للمنتجات'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'أدوات كهربائية', 'description': 'جميع أنواع الأدوات الكهربائية', 'icon': 'fa-plug'},
            {'name': 'معدات ورش', 'description': 'معدات وأدوات الورش', 'icon': 'fa-wrench'},
            {'name': 'أدوات يدوية', 'description': 'الأدوات اليدوية المختلفة', 'icon': 'fa-hammer'},
            {'name': 'معدات قياس', 'description': 'أجهزة ومعدات القياس', 'icon': 'fa-ruler'},
            {'name': 'معدات لحام', 'description': 'معدات وأدوات اللحام', 'icon': 'fa-fire'},
            {'name': 'إكسسوارات', 'description': 'إكسسوارات وقطع غيار', 'icon': 'fa-cog'},
        ]

        created_count = 0
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء الفئة: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ الفئة موجودة بالفعل: {category.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ تم إنشاء {created_count} فئة جديدة'))
