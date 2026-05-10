from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


CART_SESSION_KEY = 'cart'


def format_price(value: Decimal | int | str) -> str:
    numeric = Decimal(str(value))
    return f"{numeric:,.0f}".replace(',', ' ') + ' ₽'


def _split_description(description: str, fallback: str) -> list[str]:
    paragraphs = [part.strip() for part in description.splitlines() if part.strip()]
    if paragraphs:
        return paragraphs
    return [fallback] if fallback else ['Описание скоро появится.']


def serialize_product(product, quantity: int = 0) -> dict[str, Any]:
    category_name = product.category.name if product.category else ''
    return {
        'id': str(product.pk),
        'pk': product.pk,
        'brand': product.brand,
        'vin_number': product.vin_number,
        'name': product.name,
        'category_name': category_name,
        'short_description': product.short_description,
        'description': _split_description(product.description, product.short_description),
        'price': product.price,
        'price_display': format_price(product.price),
        'old_price': product.old_price,
        'discount_percent': product.discount_percent,
        'image_url': product.image.url if product.image else '',
        'detail_url': product.get_absolute_url(),
        'quantity': quantity,
        'in_cart': quantity > 0,
        'stock_label': 'В наличии' if product.in_stock else 'Нет в наличии',
        'stock_class': 'product-card--stock' if product.in_stock else 'product-card--low',
    }


def serialize_products(products: Iterable[Any], cart_quantities: dict[str, int] | None = None) -> list[dict[str, Any]]:
    quantities = cart_quantities or {}
    return [serialize_product(product, quantities.get(str(product.pk), 0)) for product in products]


def _get_product_model():
    from catalog.models import Product

    return Product


def _get_product_queryset():
    return _get_product_model().objects.select_related('category')


def get_product(product_id: str | None):
    if not product_id:
        return None
    product_model = _get_product_model()
    try:
        return _get_product_queryset().get(pk=product_id)
    except product_model.DoesNotExist:
        return None


class CartSession:
    def __init__(self, request):
        self.session = request.session
        self.cart: dict[str, dict[str, Any]] = self.session.setdefault(CART_SESSION_KEY, {})

    @staticmethod
    def _coerce_quantity(quantity: Any, default: int = 1) -> int:
        try:
            parsed = int(quantity)
        except (TypeError, ValueError):
            return default
        return max(1, parsed)

    @staticmethod
    def _coerce_price(value: Any, fallback: Decimal) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return fallback

    def get_quantities(self) -> dict[str, int]:
        return {product_id: item.get('quantity', 0) for product_id, item in self.cart.items()}

    def add(self, product_id: str | None, quantity: Any = 1) -> None:
        product = get_product(product_id)
        if not product:
            return

        safe_quantity = self._coerce_quantity(quantity)
        product_key = str(product.pk)
        if product_key not in self.cart:
            self.cart[product_key] = {
                'quantity': 0,
                'price_snapshot': str(product.price),
            }

        self.cart[product_key]['quantity'] += safe_quantity
        self.cart[product_key]['price_snapshot'] = self.cart[product_key].get(
            'price_snapshot',
            str(product.price),
        )
        self.session.modified = True

    def update(self, product_id: str | None, quantity: Any) -> None:
        product_key = str(product_id or '')
        if product_key not in self.cart:
            return
        self.cart[product_key]['quantity'] = self._coerce_quantity(quantity)
        self.session.modified = True

    def remove(self, product_id: str | None) -> None:
        product_key = str(product_id or '')
        if product_key in self.cart:
            del self.cart[product_key]
            self.session.modified = True

    def items(self) -> list[dict[str, Any]]:
        products = {
            str(product.pk): product
            for product in _get_product_queryset().filter(pk__in=self.cart.keys())
        }
        items: list[dict[str, Any]] = []
        for product_id, stored_item in self.cart.items():
            product = products.get(product_id)
            if not product:
                continue

            quantity = self._coerce_quantity(stored_item.get('quantity', 1))
            unit_price = self._coerce_price(stored_item.get('price_snapshot'), product.price)
            total_price = unit_price * quantity
            item = serialize_product(product, quantity)
            item.update(
                {
                    'unit_price': unit_price,
                    'unit_price_display': format_price(unit_price),
                    'total_price': total_price,
                    'total_price_display': format_price(total_price),
                }
            )
            items.append(item)
        return items

    def total(self) -> Decimal:
        return sum((item['total_price'] for item in self.items()), Decimal('0'))
