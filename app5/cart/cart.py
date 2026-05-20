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


def _normalize_source_text(*values: Any) -> str:
    return ' '.join(str(value or '').strip().lower() for value in values if value)


def _match_first_rule(source_text: str, rules: tuple[tuple[tuple[str, ...], str], ...]) -> str:
    for keywords, value in rules:
        if any(keyword in source_text for keyword in keywords):
            return value
    return ''


def _derive_characteristics(product) -> dict[str, dict[str, str]]:
    source_text = _normalize_source_text(product.name, product.short_description, product.description)
    characteristics: dict[str, dict[str, str]] = {}

    if product.vin_number:
        characteristics['vin_number'] = {
            'label': 'VIN номер',
            'value': product.vin_number,
        }

    material = _match_first_rule(
        source_text,
        (
            (('abs', 'abs-', 'abs '), 'ABS-пластик'),
            (('алюмин',), 'Алюминий'),
            (('карбон',), 'Карбон'),
            (('сталь',), 'Сталь'),
            (('кож',), 'Кожа'),
        ),
    )
    if material:
        characteristics['material'] = {
            'label': 'Материал',
            'value': material,
        }

    placement = _match_first_rule(
        source_text,
        (
            (('передн', 'front'), 'Передняя часть'),
            (('задн', 'rear'), 'Задняя часть'),
            (('порог', 'side skirt'), 'Боковая часть'),
            (('салон', 'interior'), 'Салон'),
            (('рул', 'wheel'), 'Рулевое управление'),
            (('педал', 'pedal'), 'Педальный узел'),
        ),
    )
    if placement:
        characteristics['placement'] = {
            'label': 'Расположение',
            'value': placement,
        }

    feature = _match_first_rule(
        source_text,
        (
            (('led',), 'LED'),
            (('перфорац',), 'Перфорация'),
            (('универсальн',), 'Универсальная деталь'),
            (('спортивн',), 'Спортивный стиль'),
        ),
    )
    if feature:
        characteristics['feature'] = {
            'label': 'Особенность',
            'value': feature,
        }

    return characteristics


def _serialize_saved_characteristics(product) -> dict[str, dict[str, str]]:
    raw_characteristics = getattr(product, 'characteristics', None) or {}
    if not isinstance(raw_characteristics, dict) or not raw_characteristics:
        return {}

    category = getattr(product, 'category', None)
    labels_by_key: dict[str, str] = {}
    if category is not None:
        labels_by_key = {
            definition.key: definition.name
            for definition in category.characteristics_definitions.all()
        }

    serialized: dict[str, dict[str, str]] = {}
    for key, value in raw_characteristics.items():
        serialized[str(key)] = {
            'label': labels_by_key.get(str(key), str(key).replace('_', ' ').title()),
            'value': str(value),
        }
    return serialized


def _get_product_characteristics(product) -> dict[str, dict[str, str]]:
    saved_characteristics = _serialize_saved_characteristics(product)
    return saved_characteristics or _derive_characteristics(product)


def _get_product_image_urls(product) -> list[str]:
    urls = []
    related_images = getattr(product, 'images', None)
    if related_images is not None:
        urls = [item.image.url for item in related_images.all() if getattr(item, 'image', None)]
    if not urls and product.image:
        urls = [product.image.url]
    return urls


def _serialize_compatible_vehicle(car_brand=None, car_model=None, car_generation=None) -> dict[str, str]:
    brand_name = getattr(car_brand, 'name', '') or ''
    model_name = getattr(car_model, 'name', '') or ''
    generation_name = getattr(car_generation, 'name', '') or ''
    return {
        'car_brand_id': str(getattr(car_brand, 'pk', '') or ''),
        'car_brand_name': brand_name,
        'car_model_id': str(getattr(car_model, 'pk', '') or ''),
        'car_model_name': model_name,
        'car_generation_id': str(getattr(car_generation, 'pk', '') or ''),
        'car_generation_name': generation_name,
        'label': ' '.join(
            part.strip()
            for part in [brand_name, model_name, generation_name]
            if part
        ).strip(),
    }


def _get_compatible_vehicles(product) -> list[dict[str, str]]:
    compatible_manager = getattr(product, 'compatible_vehicles', None)
    compatible_vehicles = [
        _serialize_compatible_vehicle(item.car_brand, item.car_model, item.car_generation)
        for item in compatible_manager.all()
        if compatible_manager is not None and getattr(item, 'car_brand', None)
    ] if compatible_manager is not None else []
    if compatible_vehicles:
        return compatible_vehicles
    if getattr(product, 'car_brand_id', None):
        return [
            _serialize_compatible_vehicle(
                getattr(product, 'car_brand', None),
                getattr(product, 'car_model', None),
                getattr(product, 'car_generation', None),
            ),
        ]
    return []


def _get_compatible_vehicle_label(product) -> str:
    return ', '.join(
        item['label']
        for item in _get_compatible_vehicles(product)
        if item.get('label')
    )


def _get_available_stock(product) -> int:
    stock_quantity = int(getattr(product, 'stock_quantity', 0) or 0)
    if not getattr(product, 'in_stock', False):
        return 0
    return max(0, stock_quantity)


def serialize_product(product, quantity: int = 0) -> dict[str, Any]:
    category_name = product.category.name if product.category else ''
    category_slug = product.category.slug if product.category else ''
    article = product.article or product.vin_number or product.slug or str(product.pk)
    part_number = (product.slug or article or str(product.pk)).upper()
    characteristics = _get_product_characteristics(product)
    image_urls = _get_product_image_urls(product)
    available_stock = _get_available_stock(product)
    compatible_vehicles = _get_compatible_vehicles(product)
    primary_vehicle = compatible_vehicles[0] if compatible_vehicles else {}
    return {
        'id': str(product.pk),
        'pk': product.pk,
        'brand': product.brand,
        'car_brand_id': primary_vehicle.get('car_brand_id', ''),
        'car_brand_name': primary_vehicle.get('car_brand_name', ''),
        'car_model_id': primary_vehicle.get('car_model_id', ''),
        'car_model_name': primary_vehicle.get('car_model_name', ''),
        'car_generation_id': primary_vehicle.get('car_generation_id', ''),
        'car_generation_name': primary_vehicle.get('car_generation_name', ''),
        'compatible_vehicles': compatible_vehicles,
        'compatible_vehicle': _get_compatible_vehicle_label(product),
        'vin_number': product.vin_number,
        'article': article,
        'part_number': part_number,
        'name': product.name,
        'slug': product.slug,
        'category_name': category_name,
        'category_slug': category_slug,
        'part_type': category_slug,
        'part_type_label': category_name,
        'characteristics': characteristics,
        'short_description': product.short_description,
        'description': _split_description(product.description, product.short_description),
        'price': product.price,
        'price_display': format_price(product.price),
        'old_price': product.old_price,
        'discount_percent': product.discount_percent,
        'stock_quantity': available_stock,
        'is_available': available_stock > 0,
        'image_url': image_urls[0] if image_urls else '',
        'image_urls': image_urls,
        'detail_url': product.get_absolute_url(),
        'quantity': quantity,
        'in_cart': quantity > 0,
        'stock_label': 'В наличии' if available_stock > 0 else 'Закончилось',
        'stock_class': 'product-card--stock' if available_stock > 0 else 'product-card--low',
    }


def serialize_products(products: Iterable[Any], cart_quantities: dict[str, int] | None = None) -> list[dict[str, Any]]:
    quantities = cart_quantities or {}
    return [serialize_product(product, quantities.get(str(product.pk), 0)) for product in products]


def _get_product_model():
    from catalog.models import Product

    return Product


def _get_product_queryset():
    from django.db.models import Prefetch
    from catalog.models import ProductCompatibleVehicle

    compatible_vehicles_qs = ProductCompatibleVehicle.objects.select_related(
        'car_brand',
        'car_model',
        'car_generation',
    )
    return _get_product_model().objects.select_related('category', 'car_brand', 'car_model', 'car_generation').prefetch_related(
        'images',
        'category__characteristics_definitions',
        Prefetch('compatible_vehicles', queryset=compatible_vehicles_qs),
    )


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

    def count(self) -> int:
        return sum(item.get('quantity', 0) for item in self.cart.values() if isinstance(item, dict))

    def add(self, product_id: str | None, quantity: Any = 1) -> None:
        product = get_product(product_id)
        if not product:
            return

        safe_quantity = self._coerce_quantity(quantity)
        available_stock = _get_available_stock(product)
        if available_stock <= 0:
            self.remove(product_id)
            return
        product_key = str(product.pk)
        if product_key not in self.cart:
            self.cart[product_key] = {
                'quantity': 0,
                'price_snapshot': str(product.price),
            }

        next_quantity = self.cart[product_key]['quantity'] + safe_quantity
        self.cart[product_key]['quantity'] = min(available_stock, next_quantity)
        self.cart[product_key]['price_snapshot'] = self.cart[product_key].get(
            'price_snapshot',
            str(product.price),
        )
        self.session.modified = True

    def update(self, product_id: str | None, quantity: Any) -> None:
        product_key = str(product_id or '')
        if product_key not in self.cart:
            return
        product = get_product(product_key)
        if not product:
            self.remove(product_key)
            return
        try:
            parsed_quantity = int(quantity)
        except (TypeError, ValueError):
            parsed_quantity = 1
        if parsed_quantity <= 0:
            self.remove(product_key)
            return
        available_stock = _get_available_stock(product)
        if available_stock <= 0:
            self.remove(product_key)
            return
        self.cart[product_key]['quantity'] = min(parsed_quantity, available_stock)
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
        for product_id, stored_item in list(self.cart.items()):
            product = products.get(product_id)
            if not product:
                continue

            available_stock = _get_available_stock(product)
            if available_stock <= 0:
                self.remove(product_id)
                continue

            quantity = min(self._coerce_quantity(stored_item.get('quantity', 1)), available_stock)
            if quantity != stored_item.get('quantity'):
                self.cart[product_id]['quantity'] = quantity
                self.session.modified = True
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
