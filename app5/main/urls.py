from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('basket/', views.basket, name='basket'),
    path('order/', views.order, name='order'),
    path('register/', views.legacy_register, name='legacy_register'),
    path('login/', views.legacy_login, name='legacy_login'),
]
