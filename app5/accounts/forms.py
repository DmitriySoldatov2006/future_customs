from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Электронная почта',
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'login-input',
                'placeholder': 'Электронная почта',
                'autocomplete': 'email',
            }
        ),
    )
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'login-input',
                'placeholder': 'Логин',
                'autocomplete': 'username',
            }
        ),
    )
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'login-input',
                'placeholder': 'Пароль',
                'autocomplete': 'new-password',
            }
        ),
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'login-input',
                'placeholder': 'Повторите пароль',
                'autocomplete': 'new-password',
            }
        ),
    )

    error_messages = {
        'password_mismatch': 'Пароли не совпадают',
    }

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с такой электронной почтой уже существует')
        return email


class LoginForm(forms.Form):
    email = forms.CharField(
        label='Электронная почта или логин',
        widget=forms.TextInput(
            attrs={
                'class': 'login-input',
                'placeholder': 'Электронная почта или логин',
                'autocomplete': 'username',
            }
        ),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'login-input',
                'placeholder': 'Пароль',
                'autocomplete': 'current-password',
            }
        ),
    )
