from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AccountViewsTests(TestCase):
    def test_login_get_renders_page(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вход в аккаунт')

    def test_login_redirects_authenticated_user_home(self):
        user = User.objects.create_user(username='tester', email='tester@example.com', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.get(reverse('login'))

        self.assertRedirects(response, reverse('home'))

    def test_login_with_valid_credentials_redirects_home(self):
        User.objects.create_user(username='driver', email='driver@example.com', password='StrongPass123!')

        response = self.client.post(
            reverse('login'),
            {
                'email': 'driver@example.com',
                'password': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, '/')
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_with_username_in_email_field_redirects_home(self):
        User.objects.create_user(username='driver', email='driver@example.com', password='StrongPass123!')

        response = self.client.post(
            reverse('login'),
            {
                'email': 'driver',
                'password': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, '/')
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_invalid_credentials_shows_non_field_error(self):
        User.objects.create_user(username='driver', email='driver@example.com', password='StrongPass123!')

        response = self.client.post(
            reverse('login'),
            {
                'email': 'driver@example.com',
                'password': 'wrong-password',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверная электронная почта или пароль')

    def test_login_uses_next_parameter(self):
        User.objects.create_user(username='driver', email='driver@example.com', password='StrongPass123!')

        response = self.client.post(
            reverse('login') + '?next=/cart/',
            {
                'email': 'driver@example.com',
                'password': 'StrongPass123!',
                'next': '/cart/',
            },
        )

        self.assertRedirects(response, '/cart/')

    def test_register_get_renders_page(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Регистрация')

    def test_authenticated_user_can_open_register_page(self):
        user = User.objects.create_user(username='tester', email='tester@example.com', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Регистрация')

    def test_authenticated_user_post_redirects_home(self):
        user = User.objects.create_user(username='tester', email='tester@example.com', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('register'),
            {
                'email': 'another@example.com',
                'username': 'another-user',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('home'))

    def test_register_post_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='newuser', email='newuser@example.com').exists())
        self.assertIn('_auth_user_id', self.client.session)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(username='tester', email='taken@example.com', password='StrongPass123!')

        response = self.client.post(
            reverse('register'),
            {
                'email': 'taken@example.com',
                'username': 'someone-else',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пользователь с такой электронной почтой уже существует')

    def test_register_rejects_password_mismatch(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'mismatch@example.com',
                'username': 'mismatch',
                'password1': 'StrongPass123!',
                'password2': 'WrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пароли не совпадают')
