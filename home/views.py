from django.shortcuts import render, redirect
from django.urls import reverse
from products.models import Category


def home_view(request):
    # جلب 10 أقسام فقط للصفحة الرئيسية
    categories = Category.objects.all().order_by('created_at')[:10]
    
    context = {
        'categories': categories
    }
    
    return render(request, 'home/home.html', context)

