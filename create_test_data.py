# -*- coding: utf-8 -*-
"""
Script to create test data for products, variants, and colors
"""

import os
import django
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from products.models import Category, Color, Product, ProductVariant, VariantColor, ProductVariantImage

# Delete old data (optional)
print("Deleting old data...")
ProductVariantImage.objects.all().delete()
VariantColor.objects.all().delete()
ProductVariant.objects.all().delete()
Product.objects.all().delete()
Color.objects.all().delete()
Category.objects.all().delete()

# 1. Create Category
print("Creating category...")
category = Category.objects.create(
    name="Electronics",
    description="Electronic devices and products",
    icon="fa-laptop"
)

#2. Create Colors
print("Creating colors...")
color_white = Color.objects.create(name="White", name_ar="ابيض", name_en="White", hex_code="#FFFFFF")
color_black = Color.objects.create(name="Black", name_ar="اسود", name_en="Black", hex_code="#000000")
color_red = Color.objects.create(name="Red", name_ar="احمر", name_en="Red", hex_code="#FF0000")
color_blue = Color.objects.create(name="Blue", name_ar="ازرق", name_en="Blue", hex_code="#0000FF")

# 3. Create placeholder image
print("Creating placeholder image...")
img = Image.new('RGB', (800, 800), color='#f0f0f0')
buffer = BytesIO()
img.save(buffer, format='PNG')
buffer.seek(0)
image_file = ContentFile(buffer.read(), name='placeholder.png')

# 4. Create Product with image
print("Creating product...")
product = Product.objects.create(
    name="Smart Power Strip",
    subtitle="Multi-port power strip with USB",
    description="High quality power strip with overload protection and multiple charging ports",
    category=category,
    brand="TechPro",
    is_active=True,
    is_featured=True
)
product.main_image.save('placeholder.png', image_file, save=True)

# 5. Create Variants
print("Creating variants...")

# Variant 1: 3 USB + 3 Power
variant1 = ProductVariant.objects.create(
    product=product,
    name="3 USB + 3 Power Outlets",
    code="V1-3U3P"
)

# Variant 2: 4 USB + 4 Power
variant2 = ProductVariant.objects.create(
    product=product,
    name="4 USB + 4 Power Outlets",
    code="V2-4U4P"
)

# Variant 3: 6 USB + 6 Power
variant3 = ProductVariant.objects.create(
    product=product,
    name="6 USB + 6 Power Outlets",
    code="V3-6U6P"
)

# 6. Add colors to Variant 1
print("Adding colors to Variant 1...")
VariantColor.objects.create(variant=variant1, color=color_white, price=150.00, quantity=20, sku="V1-WHITE")
VariantColor.objects.create(variant=variant1, color=color_black, price=160.00, quantity=15, sku="V1-BLACK")
VariantColor.objects.create(variant=variant1, color=color_red, price=170.00, quantity=8, sku="V1-RED")

# 7. Add colors to Variant 2
print("Adding colors to Variant 2...")
VariantColor.objects.create(variant=variant2, color=color_white, price=200.00, quantity=12, sku="V2-WHITE")
VariantColor.objects.create(variant=variant2, color=color_black, price=220.00, quantity=10, sku="V2-BLACK")
VariantColor.objects.create(variant=variant2, color=color_blue, price=210.00, quantity=5, sku="V2-BLUE")

# 8. Add colors to Variant 3
print("Adding colors to Variant 3...")
VariantColor.objects.create(variant=variant3, color=color_white, price=300.00, quantity=8, sku="V3-WHITE")
VariantColor.objects.create(variant=variant3, color=color_black, price=320.00, quantity=6, sku="V3-BLACK")

# 9. Add images to variants
print("Adding images to variants...")
for variant in [variant1, variant2, variant3]:
    # Create image for each variant
    img = Image.new('RGB', (800, 800), color='#e0e0e0')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    variant_image_file = ContentFile(buffer.read(), name=f'{variant.code}.png')
    
    ProductVariantImage.objects.create(variant=variant).image.save(f'{variant.code}.png', variant_image_file, save=True)

print("\nTest data created successfully!")
print(f"   - Product: {product.name}")
print(f"   - Number of variants: {product.variants.count()}")
print(f"   - Total colors: {VariantColor.objects.count()}")
print(f"   - Total images: {ProductVariantImage.objects.count()}")
print(f"\nOpen URL: http://127.0.0.1:8000/products/{product.slug}/")
