from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView

from .views import login_view, register_view


urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path(
        'profile/',
        login_required(TemplateView.as_view(template_name='accounts/profile.html')),
        name='profile',
    ),
]
