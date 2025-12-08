# -*- coding: utf-8 -*-
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from products.models import Product
import json

product = Product.objects.filter(slug='smart-power-strip').first()
if not product:
    print("No product found!")
else:
    print(f"Product: {product.name}")
    print(f"Min price: {product.get_min_price()}")
    print(f"Total quantity: {product.get_total_quantity()}")
    print(f"\nVariants: {product.variants.count()}")
    
    for variant in product.variants.all():
        print(f"\n  Variant: {variant.name}")
        print(f"    Code: {variant.code}")
        print(f"    Images: {variant.images.count()}")
        
        colors = variant.colors.all()
        print(f"    Colors: {colors.count()}")
        for vc in colors:
            print(f"      - {vc.color.name}: {vc.price} EGP, Qty: {vc.quantity}")
        
        images = variant.images.all()
        for img in images:
            print(f"      - Image: {img.image.url}, Color: {img.color}")
