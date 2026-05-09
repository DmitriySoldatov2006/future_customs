from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('catalog', views.catalog, name='catalog'),
    path('catalog/product', views.product_detail, name='product_detail'),
    path('create', views.create, name='create'),
    path('basket', views.basket, name='basket'),
    path('order', views.order, name='order'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
]
