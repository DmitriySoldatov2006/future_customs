from django.shortcuts import render
from .models import Articles
from .forms import ArticlesForm
from django.http import JsonResponse
import json



def index(request):
    return render(request, 'main/index.html')

def create(request):
    return render(request, 'main/create.html')

def basket(request):
    return render(request, 'main/basket.html')

def order(request):
    return render(request, 'main/order.html')

def register(request):
    return render(request, 'main/register.html')

def login(request):
    return render(request, 'main/login.html')

def catalog(request):
    return render(request, 'main/catalog.html')

def product_detail(request):
    return render(request, 'main/product_detail.html')
