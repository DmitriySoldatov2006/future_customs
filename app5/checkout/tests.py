from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product

from .models import Order


User = get_user_model()


class CheckoutFlowTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name='\u0422\u0435\u0441\u0442\u043e\u0432\u0430\u044f \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f',
            slug='checkout-category',
        )
        self.first_product = Product.objects.create(
            category=category,
            name='Brembo Prime Brake Pads Set P 85 020',
            slug='checkout-product-1',
            short_description='\u041f\u0435\u0440\u0432\u044b\u0439 \u0442\u043e\u0432\u0430\u0440',
            price='18900.00',
            in_stock=True,
        )
        self.second_product = Product.objects.create(
            category=category,
            name='MANN Oil Filter HU 816 X for Turbo Petrol Engines',
            slug='checkout-product-2',
            short_description='\u0412\u0442\u043e\u0440\u043e\u0439 \u0442\u043e\u0432\u0430\u0440',
            price='2800.00',
            in_stock=True,
        )

    def _seed_cart(self):
        self.client.post(
            reverse('cart_add'),
            {'product_id': self.first_product.pk, 'quantity': 2},
        )
        self.client.post(
            reverse('cart_add'),
            {'product_id': self.second_product.pk, 'quantity': 1},
        )

    def _valid_payload(self):
        return {
            'full_name': '\u0418\u0432\u0430\u043d\u043e\u0432 \u0418\u0432\u0430\u043d \u0418\u0432\u0430\u043d\u043e\u0432\u0438\u0447',
            'phone': '+7 (999) 123-45-67',
            'region': '\u041c\u043e\u0441\u043a\u0432\u0430',
            'city': '\u041c\u043e\u0441\u043a\u0432\u0430',
            'address': '\u0443\u043b. \u041b\u0435\u043d\u0438\u043d\u0430, \u0434. 1, \u043a\u0432. 10',
        }

    def test_checkout_redirects_to_cart_when_session_is_empty(self):
        response = self.client.get(reverse('checkout_view'))

        self.assertRedirects(response, reverse('cart_view'))

    def test_checkout_get_renders_summary_for_active_cart(self):
        self._seed_cart()

        response = self.client.get(reverse('checkout_view'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.first_product.name)
        self.assertContains(response, 'checkout-summary__item')

    def test_checkout_post_creates_order_items_and_clears_cart(self):
        self._seed_cart()

        response = self.client.post(reverse('checkout_view'), self._valid_payload())

        self.assertRedirects(response, reverse('checkout_success'))
        order = Order.objects.get()
        self.assertIsNone(order.user)
        self.assertEqual(
            order.full_name,
            '\u0418\u0432\u0430\u043d\u043e\u0432 \u0418\u0432\u0430\u043d \u0418\u0432\u0430\u043d\u043e\u0432\u0438\u0447',
        )
        self.assertEqual(order.total, Decimal('40600.00'))
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.items.get(product_id=str(self.first_product.pk)).quantity, 2)
        self.assertEqual(self.client.session.get('cart'), None)

    def test_checkout_post_attaches_authenticated_user(self):
        user = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(user)
        self._seed_cart()

        response = self.client.post(reverse('checkout_view'), self._valid_payload())

        self.assertRedirects(response, reverse('checkout_success'))
        self.assertEqual(Order.objects.get().user, user)

    def test_checkout_invalid_form_keeps_summary_and_shows_errors(self):
        self._seed_cart()

        response = self.client.post(
            reverse('checkout_view'),
            {
                'full_name': '\u0418\u0432\u0430\u043d\u043e\u0432',
                'phone': '123',
                'region': '\u041c\u043e\u0441\u043a\u0432\u0430',
                'city': '\u041c\u043e\u0441\u043a\u0432\u0430',
                'address': '\u0443\u043b. \u041b\u0435\u043d\u0438\u043d\u0430, \u0434. 1, \u043a\u0432. 10',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.first_product.name)
        self.assertContains(response, 'role="alert"')
        self.assertIn('cart', self.client.session)
