from django.urls import path

from .views import cart_add, cart_remove, cart_update, cart_view

urlpatterns = [
    path("", cart_view, name="cart_view"),
    path("add/", cart_add, name="cart_add"),
    path("remove/", cart_remove, name="cart_remove"),
    path("update/", cart_update, name="cart_update"),
]
