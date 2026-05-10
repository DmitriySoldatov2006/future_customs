from django.urls import path

from .views import checkout_success_view, checkout_view


urlpatterns = [
    path('', checkout_view, name='checkout_view'),
    path('success/', checkout_success_view, name='checkout_success'),
]
