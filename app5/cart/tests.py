from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product


class CartFlowTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name='\u0422\u0435\u0441\u0442\u043e\u0432\u0430\u044f \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f',
            slug='test-category',
        )
        self.product = Product.objects.create(
            category=category,
            name='\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0439 \u0442\u043e\u0432\u0430\u0440',
            slug='test-product',
            short_description='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435',
            price='18900.00',
            in_stock=True,
        )

    def test_cart_add_uses_session_snapshot_and_redirects(self):
        response = self.client.post(
            reverse('cart_add'),
            {'product_id': self.product.pk, 'quantity': 2},
        )

        self.assertRedirects(response, reverse('cart_view'))
        session_cart = self.client.session['cart']
        self.assertEqual(
            session_cart[str(self.product.pk)],
            {'quantity': 2, 'price_snapshot': '18900.00'},
        )

    def test_ajax_cart_add_returns_quantity_without_redirect(self):
        response = self.client.post(
            reverse('cart_add'),
            {'product_id': self.product.pk, 'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['product_id'], str(self.product.pk))
        self.assertEqual(payload['quantity'], 1)
        self.assertEqual(payload['cart_count'], 1)

    def test_cart_update_changes_quantity(self):
        self.client.post(reverse('cart_add'), {'product_id': self.product.pk, 'quantity': 1})

        response = self.client.post(
            reverse('cart_update'),
            {'product_id': self.product.pk, 'quantity': 4},
        )

        self.assertRedirects(response, reverse('cart_view'))
        self.assertEqual(self.client.session['cart'][str(self.product.pk)]['quantity'], 4)

    def test_ajax_cart_update_increments_cart_count(self):
        self.client.post(reverse('cart_add'), {'product_id': self.product.pk, 'quantity': 1})

        response = self.client.post(
            reverse('cart_update'),
            {'product_id': self.product.pk, 'quantity': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['quantity'], 2)
        self.assertEqual(payload['cart_count'], 2)

    def test_ajax_cart_update_to_zero_removes_product(self):
        self.client.post(reverse('cart_add'), {'product_id': self.product.pk, 'quantity': 1})

        response = self.client.post(
            reverse('cart_update'),
            {'product_id': self.product.pk, 'quantity': 0},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['quantity'], 0)
        self.assertEqual(payload['cart_count'], 0)
        self.assertNotIn(str(self.product.pk), self.client.session.get('cart', {}))

    def test_cart_remove_deletes_item(self):
        self.client.post(reverse('cart_add'), {'product_id': self.product.pk, 'quantity': 1})

        response = self.client.post(
            reverse('cart_remove'),
            {'product_id': self.product.pk},
        )

        self.assertRedirects(response, reverse('cart_view'))
        self.assertNotIn(str(self.product.pk), self.client.session.get('cart', {}))

    def test_cart_view_renders_empty_state(self):
        response = self.client.get(reverse('cart_view'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cart-empty')
