from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from cart.cart import format_price
from checkout.models import Order

from .forms import (
    EmailChangeForm,
    LoginForm,
    RegisterForm,
    StyledPasswordChangeForm,
    UsernameChangeForm,
)
from .models import UserProfile


User = get_user_model()


def _get_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _decorate_orders(orders):
    decorated = []
    for order in orders:
        items = list(order.items.all())
        item_names = [item.name for item in items[:3]]
        extra_count = max(0, len(items) - 3)
        decorated.append(
            {
                'order': order,
                'item_names': item_names,
                'extra_count': extra_count,
                'total_display': format_price(int(order.total)),
            }
        )
    return decorated


def _get_orders_queryset(user):
    return (
        Order.objects.filter(user=user)
        .prefetch_related('items')
        .order_by('-created_at')
    )


def register_view(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            return redirect('home')
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
            )
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['email'].strip()
            password = form.cleaned_data['password']
            user_by_identifier = User.objects.filter(email__iexact=identifier).first()

            if user_by_identifier is None:
                user_by_identifier = User.objects.filter(username__iexact=identifier).first()

            if user_by_identifier is not None:
                authenticated_user = authenticate(
                    request,
                    username=user_by_identifier.username,
                    password=password,
                )
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    next_url = request.GET.get('next') or request.POST.get('next') or '/'
                    return redirect(next_url)

            form.add_error(None, 'Неверная электронная почта или пароль')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required(login_url='/accounts/login/')
def profile_view(request):
    user = User.objects.select_related('profile').get(pk=request.user.pk)
    profile = _get_profile(user)
    orders_qs = _get_orders_queryset(user)
    order_count = orders_qs.count()
    orders = _decorate_orders(orders_qs[:10])

    context = {
        'user': user,
        'profile': profile,
        'orders': orders,
        'order_count': order_count,
        'has_more_orders': order_count > 10,
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='/accounts/login/')
@require_POST
def avatar_upload_view(request):
    uploaded_file = request.FILES.get('avatar')
    if uploaded_file is None:
        messages.error(request, 'Выберите файл для загрузки')
        return redirect('profile')

    if not (uploaded_file.content_type or '').startswith('image/'):
        messages.error(request, 'Файл должен быть изображением')
        return redirect('profile')

    if uploaded_file.size > 5 * 1024 * 1024:
        messages.error(request, 'Файл слишком большой. Максимум 5 МБ')
        return redirect('profile')

    profile = _get_profile(request.user)
    profile.avatar = uploaded_file
    profile.save()
    messages.success(request, 'Фото профиля обновлено')
    return redirect('profile')


@login_required(login_url='/accounts/login/')
def change_username_view(request):
    if request.method == 'POST':
        form = UsernameChangeForm(request.POST)
        if form.is_valid():
            new_username = form.cleaned_data['username'].strip()
            if User.objects.exclude(pk=request.user.pk).filter(username__iexact=new_username).exists():
                form.add_error('username', 'Этот логин уже занят')
            else:
                request.user.username = new_username
                request.user.save(update_fields=['username'])
                messages.success(request, 'Логин обновлён')
                return redirect('profile')
    else:
        form = UsernameChangeForm(initial={'username': request.user.username})

    return render(request, 'accounts/change_username.html', {'form': form})


@login_required(login_url='/accounts/login/')
def change_email_view(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST)
        if form.is_valid():
            new_email = form.cleaned_data['email'].strip().lower()
            if User.objects.exclude(pk=request.user.pk).filter(email__iexact=new_email).exists():
                form.add_error('email', 'Этот email уже используется')
            else:
                request.user.email = new_email
                request.user.save(update_fields=['email'])
                messages.success(request, 'Почта обновлена')
                return redirect('profile')
    else:
        form = EmailChangeForm(initial={'email': request.user.email})

    return render(request, 'accounts/change_email.html', {'form': form})


@login_required(login_url='/accounts/login/')
def change_password_view(request):
    if request.method == 'POST':
        form = StyledPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль обновлён')
            return redirect('profile')
    else:
        form = StyledPasswordChangeForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required(login_url='/accounts/login/')
def all_orders_view(request):
    user = User.objects.select_related('profile').get(pk=request.user.pk)
    profile = _get_profile(user)
    orders = _decorate_orders(_get_orders_queryset(user))

    context = {
        'user': user,
        'profile': profile,
        'orders': orders,
        'order_count': len(orders),
    }
    return render(request, 'accounts/all_orders.html', context)
