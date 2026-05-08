from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('create', views.create, name='create'),
    path('basket', views.basket, name='basket'),
    path('order', views.order, name='order'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
]
