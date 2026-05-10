from django.contrib.auth import authenticate, get_user_model, login
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm


User = get_user_model()


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
