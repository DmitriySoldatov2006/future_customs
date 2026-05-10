from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    all_orders_view,
    avatar_upload_view,
    change_email_view,
    change_password_view,
    change_username_view,
    login_view,
    profile_view,
    register_view,
)


urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/avatar/', avatar_upload_view, name='avatar_upload'),
    path('profile/change-username/', change_username_view, name='change_username'),
    path('profile/change-email/', change_email_view, name='change_email'),
    path('profile/change-password/', change_password_view, name='change_password'),
    path('orders/', all_orders_view, name='all_orders'),
]
