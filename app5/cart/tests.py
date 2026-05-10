from django.test import TestCase
from django.urls import reverse


class CartFlowTests(TestCase):
    def test_cart_add_uses_session_snapshot_and_redirects(self):
        response = self.client.post(
            reverse("cart_add"),
            {"product_id": "brembo-prime-p85-020", "quantity": 2},
        )

        self.assertRedirects(response, reverse("cart_view"))
        session_cart = self.client.session["cart"]
        self.assertEqual(
            session_cart["brembo-prime-p85-020"],
            {"quantity": 2, "price_snapshot": 18900},
        )

    def test_cart_update_changes_quantity(self):
        self.client.post(reverse("cart_add"), {"product_id": "brembo-prime-p85-020", "quantity": 1})

        response = self.client.post(
            reverse("cart_update"),
            {"product_id": "brembo-prime-p85-020", "quantity": 4},
        )

        self.assertRedirects(response, reverse("cart_view"))
        self.assertEqual(self.client.session["cart"]["brembo-prime-p85-020"]["quantity"], 4)

    def test_cart_remove_deletes_item(self):
        self.client.post(reverse("cart_add"), {"product_id": "brembo-prime-p85-020", "quantity": 1})

        response = self.client.post(
            reverse("cart_remove"),
            {"product_id": "brembo-prime-p85-020"},
        )

        self.assertRedirects(response, reverse("cart_view"))
        self.assertNotIn("brembo-prime-p85-020", self.client.session.get("cart", {}))

    def test_cart_view_renders_empty_state(self):
        response = self.client.get(reverse("cart_view"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ваша корзина пуста")
