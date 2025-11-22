from django.shortcuts import render , redirect
from django.urls import reverse




def home_view(request):

    return render(request, 'home/home.html')

