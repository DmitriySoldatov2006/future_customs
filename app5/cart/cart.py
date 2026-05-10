from __future__ import annotations

from copy import deepcopy
from typing import Any
from urllib.parse import urlencode

from django.urls import reverse

CART_SESSION_KEY = "cart"

PRODUCTS: list[dict[str, Any]] = [
    {
        "id": "brembo-prime-p85-020",
        "name": "Brembo Prime Brake Pads Set P 85 020",
        "brand": "Brembo",
        "category": "Тормозные колодки",
        "price": 18900,
        "stock_label": "В наличии",
        "stock_state": "stock",
        "short_description": "Комплект передних тормозных колодок для уверенного торможения в городе и на трассе.",
        "description": [
            "Колодки рассчитаны на стабильную работу в ежедневной эксплуатации, не перегреваются в плотном трафике и быстро выходят на рабочую температуру.",
            "Комплект подходит для европейских седанов и кроссоверов, а совместимость дополнительно подтверждается по VIN перед заказом.",
            "Состав фрикционного материала подобран так, чтобы сохранить баланс между ресурсом, тишиной и прогнозируемым торможением.",
        ],
        "meta": "Артикул P 85 020 · Передняя ось",
        "specs": [
            ("Материал", "Ceramic compound"),
            ("Датчик износа", "В комплекте"),
            ("Ось", "Передняя"),
            ("Ширина", "155.2 мм"),
            ("Толщина", "17.8 мм"),
            ("Совместимость", "BMW 3 / 4 Series, Audi A4, VW Passat"),
        ],
        "vehicles": ["BMW 320i F30", "BMW 328i F30", "BMW 420i F32", "Audi A4 B9"],
        "image": "main/images/PkAAAgPsfuA-960.jpg",
        "related_ids": [
            "ate-powerdisc-24-0325-0150-1",
            "trw-control-arm-kit",
            "mann-hu-816-x",
            "osram-night-breaker-h7",
        ],
    },
    {
        "id": "ate-powerdisc-24-0325-0150-1",
        "name": "ATE PowerDisc Front Brake Rotor 24.0325-0150.1",
        "brand": "ATE",
        "category": "Тормозные диски",
        "price": 22400,
        "stock_label": "Заканчивается",
        "stock_state": "low",
        "short_description": "Вентилируемый передний диск с направляющей канавкой для быстрого отвода пыли и воды.",
        "description": [
            "PowerDisc даёт предсказуемый отклик педали и помогает поддерживать эффективное торможение при повторных замедлениях.",
            "Рабочая поверхность устойчива к биению и подходит для штатных гражданских конфигураций без доработок суппорта.",
            "Оптимален для тех, кто хочет OEM-поведение с улучшенной стойкостью к нагреву.",
        ],
        "meta": "Артикул 24.0325-0150.1 · Передняя ось",
        "specs": [
            ("Тип", "Ventilated"),
            ("Диаметр", "312 мм"),
            ("Толщина", "25 мм"),
            ("Покрытие", "Антикоррозийное"),
            ("Комплект", "1 диск"),
            ("Совместимость", "VW Passat, Audi A4, Skoda Superb"),
        ],
        "vehicles": ["Audi A4 B9", "Volkswagen Passat B8", "Skoda Superb III"],
        "image": "main/images/bg-order-camaro.jpg",
        "related_ids": [
            "brembo-prime-p85-020",
            "trw-control-arm-kit",
            "kyb-excel-g-348006",
            "osram-night-breaker-h7",
        ],
    },
    {
        "id": "trw-control-arm-kit",
        "name": "TRW Front Control Arm Kit JTC1423 + JTC1424",
        "brand": "TRW",
        "category": "Подвеска",
        "price": 31200,
        "stock_label": "В наличии",
        "stock_state": "stock",
        "short_description": "Комплект передних рычагов с сайлентблоками и шаровыми для плотной и тихой работы подвески.",
        "description": [
            "Набор рассчитан на быстрое обновление передней подвески без подбора деталей по отдельности.",
            "Рычаги уже подготовлены к установке, а геометрия соответствует штатным параметрам для сохранения развала и кастера.",
            "Подходит для сервисного ремонта и проектов, где важен ресурс на плохом покрытии.",
        ],
        "meta": "Комплект на переднюю подвеску",
        "specs": [
            ("Комплект", "Левый + правый рычаг"),
            ("Материал", "Forged steel"),
            ("Шаровые", "Предустановлены"),
            ("Сайлентблоки", "В комплекте"),
            ("Назначение", "Front axle"),
            ("Совместимость", "BMW 3 Series F30/F31"),
        ],
        "vehicles": ["BMW 320d F30", "BMW 328i F30", "BMW 330i F31"],
        "image": "main/images/chto-takoe-avtotyuning-i-chem-on-otlichaetsya-ot-stajlinga.jpg",
        "related_ids": [
            "brembo-prime-p85-020",
            "kyb-excel-g-348006",
            "ate-powerdisc-24-0325-0150-1",
            "mann-hu-816-x",
        ],
    },
    {
        "id": "kyb-excel-g-348006",
        "name": "KYB Excel-G Rear Shock Absorber 348006",
        "brand": "KYB",
        "category": "Амортизаторы",
        "price": 14600,
        "stock_label": "В наличии",
        "stock_state": "stock",
        "short_description": "Задний газомасляный амортизатор для штатного комфорта и собранного поведения кузова.",
        "description": [
            "Серия Excel-G ориентирована на восстановление заводского характера подвески без лишней жёсткости.",
            "Амортизатор стабилизирует кузов на волнах и помогает убрать раскачку на высокой скорости.",
            "Подходит для повседневной езды и обновления подвески после уставших OEM-стоек.",
        ],
        "meta": "Артикул 348006 · Задняя ось",
        "specs": [
            ("Тип", "Газомасляный"),
            ("Ось", "Задняя"),
            ("Комплект", "1 амортизатор"),
            ("Серия", "Excel-G"),
            ("Назначение", "OEM replacement"),
            ("Совместимость", "Toyota Camry, Lexus ES"),
        ],
        "vehicles": ["Toyota Camry XV50", "Toyota Camry XV55", "Lexus ES 250"],
        "image": "main/images/arttuning-1.png",
        "related_ids": [
            "trw-control-arm-kit",
            "ate-powerdisc-24-0325-0150-1",
            "mann-hu-816-x",
            "osram-night-breaker-h7",
        ],
    },
    {
        "id": "mann-hu-816-x",
        "name": "MANN Oil Filter HU 816 X for Turbo Petrol Engines",
        "brand": "MANN-FILTER",
        "category": "Фильтры",
        "price": 2800,
        "stock_label": "Заканчивается",
        "stock_state": "low",
        "short_description": "Картриджный масляный фильтр для турбированных бензиновых двигателей с точной посадкой.",
        "description": [
            "Фильтрующий элемент удерживает мелкие частицы и помогает сохранить давление масла в длинных межсервисных интервалах.",
            "Производитель делает упор на стабильный поток масла даже на холодном пуске.",
            "Часто используется при сервисном обслуживании современных VAG и BMW моторов.",
        ],
        "meta": "Артикул HU 816 X · TO и сервис",
        "specs": [
            ("Тип", "Картридж"),
            ("Назначение", "Масляная система"),
            ("Материал", "Синтетическое волокно"),
            ("Комплект", "Фильтр + уплотнения"),
            ("Интервал", "По регламенту ТО"),
            ("Совместимость", "VAG 2.0 TSI, BMW B48"),
        ],
        "vehicles": ["Volkswagen Golf GTI", "Skoda Octavia RS", "BMW 330i G20"],
        "image": "main/images/f7b63bd4-b7ba-49a3-a2f6-e60b12d8cdc8.png",
        "related_ids": [
            "osram-night-breaker-h7",
            "brembo-prime-p85-020",
            "kyb-excel-g-348006",
            "ate-powerdisc-24-0325-0150-1",
        ],
    },
    {
        "id": "osram-night-breaker-h7",
        "name": "Osram Night Breaker Laser H7 Twin Pack",
        "brand": "Osram",
        "category": "Освещение",
        "price": 5400,
        "stock_label": "В наличии",
        "stock_state": "stock",
        "short_description": "Комплект ламп H7 с более ярким световым пучком и уверенной подсветкой в плохую погоду.",
        "description": [
            "Night Breaker Laser улучшает дальность обзора и делает световой рисунок плотнее без перехода на нештатные решения.",
            "Хороший вариант для тех, кто хочет освежить свет фар перед поездками по трассе.",
            "Лампы поставляются парой и подходят для быстрой замены обеих сторон сразу.",
        ],
        "meta": "Цоколь H7 · Комплект 2 шт.",
        "specs": [
            ("Цоколь", "H7"),
            ("Комплект", "2 лампы"),
            ("Назначение", "Ближний / дальний свет"),
            ("Цвет", "Cool white"),
            ("Напряжение", "12V"),
            ("Совместимость", "Любые H7-приложения"),
        ],
        "vehicles": ["Volkswagen Polo", "Skoda Octavia", "BMW 5 Series F10"],
        "image": "main/images/bg-order-camaro.jpg",
        "related_ids": [
            "mann-hu-816-x",
            "brembo-prime-p85-020",
            "ate-powerdisc-24-0325-0150-1",
            "kyb-excel-g-348006",
        ],
    },
]

PRODUCTS_BY_ID = {product["id"]: product for product in PRODUCTS}
DEFAULT_PRODUCT_ID = PRODUCTS[0]["id"]


def format_price(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₽"


def _detail_url(product_id: str) -> str:
    return f"{reverse('product_detail')}?{urlencode({'product': product_id})}"


def _serialize_product(product: dict[str, Any], quantity: int = 0) -> dict[str, Any]:
    item = deepcopy(product)
    item["detail_url"] = _detail_url(item["id"])
    item["price_display"] = format_price(item["price"])
    item["quantity"] = quantity
    item["in_cart"] = quantity > 0
    item["stock_class"] = f"product-card--{item['stock_state']}"
    return item


def get_product(product_id: str | None) -> dict[str, Any] | None:
    if not product_id:
        return None
    product = PRODUCTS_BY_ID.get(product_id)
    if not product:
        return None
    return _serialize_product(product)


def get_catalog_products(cart_quantities: dict[str, int] | None = None) -> list[dict[str, Any]]:
    quantities = cart_quantities or {}
    return [_serialize_product(product, quantities.get(product["id"], 0)) for product in PRODUCTS]


def get_related_products(product_id: str, cart_quantities: dict[str, int] | None = None) -> list[dict[str, Any]]:
    product = PRODUCTS_BY_ID.get(product_id) or PRODUCTS_BY_ID[DEFAULT_PRODUCT_ID]
    quantities = cart_quantities or {}
    return [
        _serialize_product(PRODUCTS_BY_ID[related_id], quantities.get(related_id, 0))
        for related_id in product["related_ids"]
        if related_id in PRODUCTS_BY_ID
    ]


class CartSession:
    def __init__(self, request):
        self.session = request.session
        self.cart: dict[str, dict[str, int]] = self.session.setdefault(CART_SESSION_KEY, {})

    @staticmethod
    def _coerce_quantity(quantity: Any, default: int = 1) -> int:
        try:
            parsed = int(quantity)
        except (TypeError, ValueError):
            return default
        return max(1, parsed)

    def get_quantities(self) -> dict[str, int]:
        return {product_id: item.get("quantity", 0) for product_id, item in self.cart.items()}

    def add(self, product_id: str | None, quantity: Any = 1) -> None:
        product = PRODUCTS_BY_ID.get(product_id or "")
        if not product:
            return

        safe_quantity = self._coerce_quantity(quantity)
        product_key = str(product["id"])
        if product_key not in self.cart:
            self.cart[product_key] = {
                "quantity": 0,
                "price_snapshot": product["price"],
            }

        self.cart[product_key]["quantity"] += safe_quantity
        self.cart[product_key]["price_snapshot"] = self.cart[product_key].get("price_snapshot", product["price"])
        self.session.modified = True

    def update(self, product_id: str | None, quantity: Any) -> None:
        product_key = str(product_id or "")
        if product_key not in self.cart:
            return
        self.cart[product_key]["quantity"] = self._coerce_quantity(quantity)
        self.session.modified = True

    def remove(self, product_id: str | None) -> None:
        product_key = str(product_id or "")
        if product_key in self.cart:
            del self.cart[product_key]
            self.session.modified = True

    def items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for product_id, stored_item in self.cart.items():
            product = PRODUCTS_BY_ID.get(product_id)
            if not product:
                continue

            quantity = self._coerce_quantity(stored_item.get("quantity", 1))
            unit_price = int(stored_item.get("price_snapshot", product["price"]))
            total_price = unit_price * quantity
            item = _serialize_product(product, quantity)
            item.update(
                {
                    "unit_price": unit_price,
                    "unit_price_display": format_price(unit_price),
                    "total_price": total_price,
                    "total_price_display": format_price(total_price),
                }
            )
            items.append(item)
        return items

    def total(self) -> int:
        return sum(item["total_price"] for item in self.items())
