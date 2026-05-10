from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Order


User = get_user_model()


class CheckoutFlowTests(TestCase):
    def _seed_cart(self):
        self.client.post(
            reverse('cart_add'),
            {'product_id': 'brembo-prime-p85-020', 'quantity': 2},
        )
        self.client.post(
            reverse('cart_add'),
            {'product_id': 'mann-hu-816-x', 'quantity': 1},
        )

    def _valid_payload(self):
        return {
            'full_name': 'Иванов Иван Иванович',
            'phone': '+7 (999) 123-45-67',
            'region': 'Московская область',
            'city': 'Москва',
            'address': 'ул. Ленина, д. 1, кв. 10',
        }

    def test_checkout_redirects_to_cart_when_session_is_empty(self):
        response = self.client.get(reverse('checkout_view'))

        self.assertRedirects(response, reverse('cart_view'))

    def test_checkout_get_renders_summary_for_active_cart(self):
        self._seed_cart()

        response = self.client.get(reverse('checkout_view'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Оформление заказа')
        self.assertContains(response, 'Ваш заказ')
        self.assertContains(response, 'Brembo Prime Brake Pads Set P 85 020')

    def test_checkout_post_creates_order_items_and_clears_cart(self):
        self._seed_cart()

        response = self.client.post(reverse('checkout_view'), self._valid_payload())

        self.assertRedirects(response, reverse('checkout_success'))
        order = Order.objects.get()
        self.assertIsNone(order.user)
        self.assertEqual(order.full_name, 'Иванов Иван Иванович')
        self.assertEqual(order.total, Decimal('40600.00'))
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.items.get(product_id='brembo-prime-p85-020').quantity, 2)
        self.assertEqual(self.client.session.get('cart'), None)

    def test_checkout_post_attaches_authenticated_user(self):
        user = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(user)
        self._seed_cart()

        self.client.post(reverse('checkout_view'), self._valid_payload())

        self.assertEqual(Order.objects.get().user, user)

    def test_checkout_invalid_form_keeps_summary_and_shows_errors(self):
        self._seed_cart()

        response = self.client.post(
            reverse('checkout_view'),
            {
                'full_name': 'Иванов',
                'phone': '123',
                'region': 'Московская область',
                'city': 'Москва',
                'address': 'ул. Ленина, д. 1, кв. 10',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите полное ФИО')
        self.assertContains(response, 'Введите корректный номер телефона')
        self.assertContains(response, 'Ваш заказ')
        self.assertIn('cart', self.client.session)
