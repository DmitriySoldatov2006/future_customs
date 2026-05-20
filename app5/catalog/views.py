import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from cart.cart import CartSession, serialize_product, serialize_products
from checkout.models import Order, OrderItem

from .models import Brand, CarBrand, CarGeneration, CarModel, Category, CategoryCharacteristic, CategoryCharacteristicOption, Product, ProductCompatibleVehicle, ProductImage


def _build_catalog_select_options(serialized_products):
    part_types = sorted(
        {
            (
                product.get('part_type', '').strip(),
                product.get('part_type_label', '').strip() or product.get('category_name', '').strip(),
            )
            for product in serialized_products
            if product.get('part_type')
        },
        key=lambda item: item[1] or item[0],
    )
    brands = sorted(
        {str(product.get('brand', '')).strip() for product in serialized_products if product.get('brand')},
    )
    return {
        'part_type_options': [
            {'value': value, 'label': label or value}
            for value, label in part_types
        ],
        'brand_options': [
            {'value': brand, 'label': brand}
            for brand in brands
        ],
    }


def _catalog_queryset():
    compatible_vehicles_qs = ProductCompatibleVehicle.objects.select_related(
        'car_brand',
        'car_model',
        'car_generation',
    )
    return Product.objects.select_related('category', 'car_brand', 'car_model', 'car_generation').prefetch_related(
        'images',
        'category__characteristics_definitions',
        Prefetch('compatible_vehicles', queryset=compatible_vehicles_qs),
    )


def _json_payload(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _parse_json_string(value, fallback):
    try:
        return json.loads(value or '')
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _parse_admin_price(raw_value):
    normalized = str(raw_value or '').strip().replace(' ', '').replace(',', '.')
    if not normalized:
        raise ValueError('Укажите цену товара.')
    try:
        price = Decimal(normalized)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('Укажите корректную цену товара.')
    if price < 0:
        raise ValueError('Цена товара не может быть отрицательной.')
    return price.quantize(Decimal('0.01'))


def _parse_stock_quantity(raw_value):
    normalized = str(raw_value or '').strip()
    if not normalized:
        raise ValueError('Укажите количество товара в наличии.')
    try:
        quantity = int(normalized)
    except (TypeError, ValueError):
        raise ValueError('Укажите корректное количество товара в наличии.')
    if quantity < 0:
        raise ValueError('Количество товара в наличии не может быть отрицательным.')
    return quantity


def _parse_order_item_quantity(raw_value):
    normalized = str(raw_value or '').strip()
    if not normalized:
        raise ValueError('Укажите количество товара в заказе.')
    try:
        quantity = int(normalized)
    except (TypeError, ValueError):
        raise ValueError('Укажите корректное количество товара в заказе.')
    if quantity <= 0:
        raise ValueError('Количество товара в заказе должно быть больше нуля.')
    return quantity


def _unique_slug(model, source_value, *, slug_field='slug', queryset=None):
    base_slug = slugify(source_value or '')[:240] or 'item'
    current_queryset = queryset if queryset is not None else model.objects.all()
    candidate = base_slug
    index = 2
    while current_queryset.filter(**{slug_field: candidate}).exists():
        candidate = f'{base_slug[:230]}-{index}'
        index += 1
    return candidate


def _unique_characteristic_key(category, name):
    return _unique_slug(
        CategoryCharacteristic,
        name,
        slug_field='key',
        queryset=CategoryCharacteristic.objects.filter(category=category),
    )


def _serialize_part_type(category):
    return {
        'id': category.pk,
        'name': category.name,
        'slug': category.slug,
        'characteristics': [
            {
                'id': definition.pk,
                'name': definition.name,
                'key': definition.key,
                'allows_custom_value': definition.allows_custom_value,
                'values': [option.value for option in definition.options.all()],
            }
            for definition in category.characteristics_definitions.all()
        ],
    }


def _serialize_brand(brand):
    return {
        'id': brand.pk,
        'name': brand.name,
    }


def _serialize_admin_product_image(product_image):
    try:
        image_url = product_image.image.url
    except ValueError:
        image_url = ''

    return {
        'id': product_image.pk,
        'name': product_image.image.name.rsplit('/', 1)[-1],
        'url': image_url,
        'sort_order': product_image.sort_order,
        'is_primary': bool(product_image.product.image and product_image.product.image.name == product_image.image.name),
    }


def _serialize_car_brand(brand):
    return {
        'id': brand.pk,
        'name': brand.name,
        'models': [_serialize_car_model(model) for model in brand.models.all()],
    }


def _serialize_car_model(model):
    return {
        'id': model.pk,
        'name': model.name,
        'brand_id': model.brand_id,
        'brand_name': model.brand.name,
        'generations': [_serialize_car_generation(generation) for generation in model.generations.all()],
    }


def _serialize_car_generation(generation):
    return {
        'id': generation.pk,
        'name': generation.name,
        'model_id': generation.model_id,
        'model_name': generation.model.name,
        'brand_id': generation.model.brand_id,
        'brand_name': generation.model.brand.name,
    }


def _build_compatible_vehicle_label(brand_name='', model_name='', generation_name=''):
    parts = [brand_name or '', model_name or '', generation_name or '']
    return ' '.join(part.strip() for part in parts if part).strip()


def _serialize_product_compatible_vehicle(car_brand=None, car_model=None, car_generation=None):
    brand_name = car_brand.name if car_brand else ''
    model_name = car_model.name if car_model else ''
    generation_name = car_generation.name if car_generation else ''
    return {
        'car_brand_id': car_brand.pk if car_brand else '',
        'car_brand_name': brand_name,
        'car_model_id': car_model.pk if car_model else '',
        'car_model_name': model_name,
        'car_generation_id': car_generation.pk if car_generation else '',
        'car_generation_name': generation_name,
        'label': _build_compatible_vehicle_label(brand_name, model_name, generation_name),
    }


def _get_product_compatible_vehicles(product):
    compatible_manager = getattr(product, 'compatible_vehicles', None)
    compatible_vehicles = [
        _serialize_product_compatible_vehicle(item.car_brand, item.car_model, item.car_generation)
        for item in compatible_manager.all()
        if compatible_manager is not None and getattr(item, 'car_brand', None)
    ] if compatible_manager is not None else []
    if compatible_vehicles:
        return compatible_vehicles
    if product.car_brand_id:
        return [
            _serialize_product_compatible_vehicle(
                product.car_brand,
                product.car_model,
                product.car_generation,
            ),
        ]
    return []


def _parse_product_compatible_vehicles(payload, *, is_multipart=False):
    raw_vehicles = (
        _parse_json_string(payload.get('compatible_vehicles'), [])
        if is_multipart
        else payload.get('compatible_vehicles')
    )
    if isinstance(raw_vehicles, list) and raw_vehicles:
        return raw_vehicles

    legacy_vehicle = {
        'car_brand_id': payload.get('car_brand_id'),
        'car_model_id': payload.get('car_model_id'),
        'car_generation_id': payload.get('car_generation_id'),
    }
    if any(legacy_vehicle.values()):
        return [legacy_vehicle]
    return []


def _parse_removed_product_image_ids(payload, *, is_multipart=False):
    raw_ids = (
        _parse_json_string(payload.get('remove_image_ids'), [])
        if is_multipart
        else payload.get('remove_image_ids')
    )
    if not isinstance(raw_ids, list):
        return []

    normalized_ids = []
    seen = set()
    for raw_id in raw_ids:
        try:
            image_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if image_id <= 0 or image_id in seen:
            continue
        seen.add(image_id)
        normalized_ids.append(image_id)
    return normalized_ids


def _resolve_product_compatible_vehicles(raw_vehicles):
    resolved = []
    seen = set()

    for index, raw_item in enumerate(raw_vehicles or []):
        item = raw_item or {}
        brand_id = item.get('car_brand_id') or item.get('brand_id') or ''
        model_id = item.get('car_model_id') or item.get('model_id') or ''
        generation_id = item.get('car_generation_id') or item.get('generation_id') or ''

        if not any([brand_id, model_id, generation_id]):
            continue
        if not brand_id:
            raise ValueError('Выберите марку автомобиля для совместимости.')

        try:
            car_brand = CarBrand.objects.get(pk=brand_id)
        except CarBrand.DoesNotExist as error:
            raise ValueError('Выберите корректную марку автомобиля.') from error

        car_model = None
        car_generation = None
        if model_id:
            try:
                car_model = CarModel.objects.select_related('brand').get(pk=model_id)
            except CarModel.DoesNotExist as error:
                raise ValueError('Выберите корректную модель автомобиля.') from error
            if car_model.brand_id != car_brand.pk:
                raise ValueError('Выберите корректную модель автомобиля.')
        elif generation_id:
            raise ValueError('Выберите модель автомобиля для выбранного поколения.')

        if generation_id:
            try:
                car_generation = CarGeneration.objects.select_related('model__brand').get(pk=generation_id)
            except CarGeneration.DoesNotExist as error:
                raise ValueError('Выберите корректное поколение автомобиля.') from error
            if car_model is None or car_generation.model_id != car_model.pk:
                raise ValueError('Выберите корректное поколение автомобиля.')

        dedupe_key = (
            car_brand.pk,
            car_model.pk if car_model else None,
            car_generation.pk if car_generation else None,
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        resolved.append(
            {
                'car_brand': car_brand,
                'car_model': car_model,
                'car_generation': car_generation,
                'sort_order': index,
            },
        )

    return resolved


def _assign_primary_product_compatible_vehicle(product, compatible_vehicles):
    primary = compatible_vehicles[0] if compatible_vehicles else None
    product.car_brand = primary['car_brand'] if primary else None
    product.car_model = primary['car_model'] if primary else None
    product.car_generation = primary['car_generation'] if primary else None


def _replace_product_compatible_vehicles(product, compatible_vehicles):
    product.compatible_vehicles.all().delete()
    ProductCompatibleVehicle.objects.bulk_create(
        [
            ProductCompatibleVehicle(
                product=product,
                car_brand=item['car_brand'],
                car_model=item['car_model'],
                car_generation=item['car_generation'],
                sort_order=item['sort_order'],
            )
            for item in compatible_vehicles
        ],
    )


def _replace_product_images(product, *, uploaded_images=None, remove_image_ids=None):
    uploaded_images = list(uploaded_images or [])
    remove_image_ids = set(remove_image_ids or [])

    if remove_image_ids:
        for product_image in product.images.filter(pk__in=remove_image_ids):
            product_image.image.delete(save=False)
            product_image.delete()

    existing_images = list(product.images.order_by('sort_order', 'pk'))
    next_sort_order = len(existing_images)
    for index, uploaded_image in enumerate(uploaded_images):
        ProductImage.objects.create(
            product=product,
            image=uploaded_image,
            sort_order=next_sort_order + index,
        )

    refreshed_images = list(product.images.order_by('sort_order', 'pk'))
    for index, product_image in enumerate(refreshed_images):
        if product_image.sort_order != index:
            ProductImage.objects.filter(pk=product_image.pk).update(sort_order=index)
            product_image.sort_order = index

    current_primary = product.image.name if product.image else ''
    next_primary = refreshed_images[0].image.name if refreshed_images else ''
    if current_primary != next_primary:
        product.image = next_primary or None
        product.save(update_fields=['image'])


def _serialize_admin_product(product):
    brand = Brand.objects.filter(name=product.brand).only('pk').first() if product.brand else None
    compatible_vehicles = _get_product_compatible_vehicles(product)
    primary_vehicle = compatible_vehicles[0] if compatible_vehicles else {}
    return {
        'id': product.pk,
        'name': product.name,
        'short_description': product.short_description,
        'description': product.description,
        'article': product.article,
        'vin_number': product.vin_number,
        'price': str(product.price),
        'stock_quantity': product.stock_quantity,
        'brand': product.brand,
        'brand_id': brand.pk if brand else '',
        'car_brand_id': primary_vehicle.get('car_brand_id', ''),
        'car_brand_name': primary_vehicle.get('car_brand_name', ''),
        'car_model_id': primary_vehicle.get('car_model_id', ''),
        'car_model_name': primary_vehicle.get('car_model_name', ''),
        'car_generation_id': primary_vehicle.get('car_generation_id', ''),
        'car_generation_name': primary_vehicle.get('car_generation_name', ''),
        'compatible_vehicles': compatible_vehicles,
        'compatible_vehicle': ', '.join(
            item['label']
            for item in compatible_vehicles
            if item.get('label')
        ),
        'category_id': product.category_id or '',
        'category_name': product.category.name if product.category else '',
        'characteristics': product.characteristics or {},
        'images': [
            _serialize_admin_product_image(product_image)
            for product_image in product.images.all()
        ],
    }


def _serialize_admin_order_item(item):
    return {
        'id': item.pk,
        'product_id': item.product_id,
        'name': item.name,
        'quantity': item.quantity,
        'price': str(item.price),
    }


def _serialize_admin_order(order):
    items = list(order.items.all())
    return {
        'id': order.pk,
        'full_name': order.full_name,
        'phone': order.phone,
        'region': order.region,
        'city': order.city,
        'address': order.address,
        'total': str(order.total),
        'status': order.status,
        'created_at': order.created_at.isoformat(),
        'created_at_display': order.created_at.strftime('%d.%m.%Y %H:%M'),
        'items_count': len(items),
        'items_summary': ', '.join(item.name for item in items[:3]),
        'items': [_serialize_admin_order_item(item) for item in items],
    }


def _serialize_admin_user(user):
    orders = getattr(user, 'admin_orders', None)
    if orders is None:
        orders = (
            Order.objects.filter(user=user)
            .prefetch_related('items')
            .order_by('-created_at')
        )
    return {
        'id': user.pk,
        'name': user.username,
        'email': user.email,
        'role': 'admin' if user.is_superuser or user.is_staff else 'user',
        'orders': [_serialize_admin_order(order) for order in orders],
    }


def _sync_admin_user_orders(user, orders_payload):
    if orders_payload is None:
        return
    if not isinstance(orders_payload, list):
        raise ValueError('Укажите корректную историю заказов.')

    orders_by_id = {
        str(order.pk): order
        for order in Order.objects.filter(user=user).prefetch_related('items')
    }
    seen_order_ids = set()

    for raw_order in orders_payload:
        if not isinstance(raw_order, dict):
            raise ValueError('Укажите корректную историю заказов.')

        order_id = str(raw_order.get('id') or '').strip()
        if not order_id or order_id not in orders_by_id:
            raise ValueError('Выберите корректный заказ пользователя.')
        if order_id in seen_order_ids:
            raise ValueError('История заказов содержит дублирующиеся заказы.')
        seen_order_ids.add(order_id)

        order = orders_by_id[order_id]
        full_name = str(raw_order.get('full_name') or '').strip()
        phone = str(raw_order.get('phone') or '').strip()
        region = str(raw_order.get('region') or '').strip()
        city = str(raw_order.get('city') or '').strip()
        address = str(raw_order.get('address') or '').strip()
        status = str(raw_order.get('status') or '').strip()

        if not full_name:
            raise ValueError(f'Укажите ФИО для заказа #{order.pk}.')
        if not phone:
            raise ValueError(f'Укажите телефон для заказа #{order.pk}.')
        if not region:
            raise ValueError(f'Укажите регион для заказа #{order.pk}.')
        if not city:
            raise ValueError(f'Укажите город для заказа #{order.pk}.')
        if not address:
            raise ValueError(f'Укажите адрес для заказа #{order.pk}.')
        if not status:
            raise ValueError(f'Укажите статус для заказа #{order.pk}.')

        items_payload = raw_order.get('items')
        if not isinstance(items_payload, list) or not items_payload:
            raise ValueError(f'Укажите товары для заказа #{order.pk}.')

        new_items = []
        for raw_item in items_payload:
            if not isinstance(raw_item, dict):
                raise ValueError(f'Укажите корректные товары для заказа #{order.pk}.')

            item_name = str(raw_item.get('name') or '').strip()
            if not item_name:
                raise ValueError(f'Укажите название товара в заказе #{order.pk}.')

            new_items.append(
                OrderItem(
                    order=order,
                    product_id=str(raw_item.get('product_id') or '').strip(),
                    name=item_name,
                    quantity=_parse_order_item_quantity(raw_item.get('quantity')),
                    price=_parse_admin_price(raw_item.get('price')),
                ),
            )

        order.full_name = full_name
        order.phone = phone
        order.region = region
        order.city = city
        order.address = address
        order.status = status
        order.total = _parse_admin_price(raw_order.get('total'))
        order.save(update_fields=['full_name', 'phone', 'region', 'city', 'address', 'status', 'total'])
        order.items.all().delete()
        OrderItem.objects.bulk_create(new_items)

    for order_id, order in orders_by_id.items():
        if order_id not in seen_order_ids:
            order.delete()


def _build_admin_panel_context():
    categories = Category.objects.prefetch_related(
        'characteristics_definitions__options',
    ).order_by('name')
    brands = Brand.objects.order_by('name')
    car_brands = CarBrand.objects.prefetch_related('models__generations').order_by('name')
    return {
        'admin_panel_brands': [
            _serialize_brand(brand)
            for brand in brands
        ],
        'admin_panel_part_types': [
            _serialize_part_type(category)
            for category in categories
        ],
        'admin_panel_car_brands': [
            _serialize_car_brand(brand)
            for brand in car_brands
        ],
    }


def _replace_part_type_characteristics(category, raw_characteristics):
    category.characteristics_definitions.all().delete()

    for index, raw_characteristic in enumerate(raw_characteristics):
        characteristic_name = str((raw_characteristic or {}).get('name') or '').strip()
        if not characteristic_name:
            continue

        raw_values = (raw_characteristic or {}).get('values') or []
        allows_custom_value = any(
            bool((value_item or {}).get('is_custom'))
            for value_item in raw_values
        )

        definition = CategoryCharacteristic.objects.create(
            category=category,
            name=characteristic_name,
            key=_unique_characteristic_key(category, characteristic_name),
            allows_custom_value=allows_custom_value,
            sort_order=index,
        )

        if allows_custom_value:
            continue

        seen_values = set()
        for value_index, raw_value in enumerate(raw_values):
            value = str((raw_value or {}).get('value') or '').strip()
            if not value or value in seen_values:
                continue
            seen_values.add(value)
            CategoryCharacteristicOption.objects.create(
                characteristic=definition,
                value=value,
                sort_order=value_index,
            )


def _validate_product_characteristics(category, raw_characteristics):
    if not isinstance(raw_characteristics, dict):
        return {}

    definitions = {
        definition.key: definition
        for definition in category.characteristics_definitions.prefetch_related('options').all()
    }
    cleaned = {}
    for key, raw_value in raw_characteristics.items():
        definition = definitions.get(str(key))
        if definition is None:
            continue

        value = str(raw_value or '').strip()
        if not value:
            continue

        if definition.allows_custom_value:
            cleaned[definition.key] = value
            continue

        allowed_values = {option.value for option in definition.options.all()}
        if value in allowed_values:
            cleaned[definition.key] = value
    return cleaned


def catalog_view(request):
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    products = _catalog_queryset().all()

    cart_quantities = CartSession(request).get_quantities()
    serialized_products = serialize_products(products, cart_quantities)
    select_options = _build_catalog_select_options(serialized_products)

    context = {
        'products': serialized_products,
        'categories': categories,
        'active_category': category_slug,
        'results_count': len(serialized_products),
        'search_query': search_query,
        **select_options,
    }
    return render(request, 'catalog/catalog.html', context)


def product_detail_view(request, slug):
    cart_quantities = CartSession(request).get_quantities()
    product_obj = get_object_or_404(_catalog_queryset(), slug=slug)
    product = serialize_product(product_obj, cart_quantities.get(str(product_obj.pk), 0))
    related = serialize_products(
        _catalog_queryset()
        .filter(category=product_obj.category)
        .exclude(pk=product_obj.pk)[:4],
        cart_quantities,
    )
    context = {
        'product': product,
        'related_products': related,
    }
    return render(request, 'catalog/product_detail.html', context)


@require_GET
def admin_panel_view(request):
    return render(request, 'catalog/admin_panel.html', _build_admin_panel_context())


@require_http_methods(['GET', 'POST'])
def admin_panel_create_brand_view(request):
    if request.method == 'GET':
        brands = Brand.objects.order_by('name')
        return JsonResponse({'ok': True, 'brands': [_serialize_brand(brand) for brand in brands]})

    payload = _json_payload(request)
    name = str(payload.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите название производителя.'}, status=400)

    brand, created = Brand.objects.get_or_create(name=name)
    return JsonResponse(
        {
            'ok': True,
            'created': created,
            'brand': _serialize_brand(brand),
        },
    )


@require_http_methods(['GET', 'POST'])
def admin_panel_create_part_type_view(request):
    if request.method == 'GET':
        categories = Category.objects.prefetch_related('characteristics_definitions__options').order_by('name')
        return JsonResponse({'ok': True, 'part_types': [_serialize_part_type(category) for category in categories]})

    payload = _json_payload(request)
    name = str(payload.get('name') or '').strip()
    characteristics = payload.get('characteristics') or []

    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите тип товара.'}, status=400)

    with transaction.atomic():
        category = Category.objects.create(
            name=name,
            slug=_unique_slug(Category, name),
        )
        _replace_part_type_characteristics(category, characteristics)

        category = Category.objects.prefetch_related(
            'characteristics_definitions__options',
        ).get(pk=category.pk)

    return JsonResponse(
        {
            'ok': True,
            'part_type': _serialize_part_type(category),
        },
    )


@require_http_methods(['GET', 'POST'])
def admin_panel_create_product_view(request):
    if request.method == 'GET':
        products = _catalog_queryset().all()
        return JsonResponse({'ok': True, 'products': [_serialize_admin_product(product) for product in products]})

    is_multipart = 'multipart/form-data' in (request.content_type or '')
    payload = request.POST if is_multipart else _json_payload(request)
    name = str(payload.get('name') or '').strip()
    short_description = str(payload.get('short_description') or '').strip()
    description = str(payload.get('description') or '').strip()
    article = str(payload.get('article') or '').strip()
    vin_number = str(payload.get('vin_number') or '').strip()
    raw_price = payload.get('price')
    raw_stock_quantity = payload.get('stock_quantity')
    brand_id = payload.get('brand_id')
    compatible_vehicles_payload = _parse_product_compatible_vehicles(payload, is_multipart=is_multipart)
    category_id = payload.get('category_id')
    raw_characteristics = (
        _parse_json_string(payload.get('characteristics'), {})
        if is_multipart
        else payload.get('characteristics') or {}
    )
    uploaded_images = list(request.FILES.getlist('images')) if is_multipart else []

    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите название товара.'}, status=400)
    if not category_id:
        return JsonResponse({'ok': False, 'error': 'Выберите тип товара.'}, status=400)
    if not brand_id:
        return JsonResponse({'ok': False, 'error': 'Выберите производителя.'}, status=400)
    try:
        price = _parse_admin_price(raw_price)
    except ValueError as error:
        return JsonResponse({'ok': False, 'error': str(error)}, status=400)
    try:
        stock_quantity = _parse_stock_quantity(raw_stock_quantity)
    except ValueError as error:
        return JsonResponse({'ok': False, 'error': str(error)}, status=400)

    category = get_object_or_404(
        Category.objects.prefetch_related('characteristics_definitions__options'),
        pk=category_id,
    )
    brand = get_object_or_404(Brand, pk=brand_id)
    try:
        compatible_vehicles = _resolve_product_compatible_vehicles(compatible_vehicles_payload)
    except ValueError as error:
        return JsonResponse({'ok': False, 'error': str(error)}, status=400)
    car_brand = compatible_vehicles[0]['car_brand'] if compatible_vehicles else None
    car_model = compatible_vehicles[0]['car_model'] if compatible_vehicles else None
    car_generation = compatible_vehicles[0]['car_generation'] if compatible_vehicles else None
    if car_model and (car_brand is None or car_model.brand_id != car_brand.pk):
        return JsonResponse({'ok': False, 'error': 'Выберите корректную модель автомобиля.'}, status=400)
    if car_generation and (car_model is None or car_generation.model_id != car_model.pk):
        return JsonResponse({'ok': False, 'error': 'Выберите корректное поколение автомобиля.'}, status=400)
    characteristics = _validate_product_characteristics(category, raw_characteristics)

    with transaction.atomic():
        product = Product.objects.create(
            category=category,
            car_brand=car_brand,
            car_model=car_model,
            car_generation=car_generation,
            brand=brand.name,
            article=article,
            vin_number=vin_number,
            name=name,
            slug=_unique_slug(Product, article or name),
            short_description=short_description,
            description=description,
            characteristics=characteristics,
            price=price,
            stock_quantity=stock_quantity,
            in_stock=stock_quantity > 0,
        )
        _replace_product_compatible_vehicles(product, compatible_vehicles)
        _replace_product_images(product, uploaded_images=uploaded_images)

    return JsonResponse(
        {
            'ok': True,
            'product': {
                'id': product.pk,
                'name': product.name,
                'slug': product.slug,
                'images_count': len(uploaded_images),
            },
        },
    )


@require_POST
def admin_panel_update_brand_view(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)
    payload = _json_payload(request)
    name = str(payload.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите название производителя.'}, status=400)
    if Brand.objects.exclude(pk=brand.pk).filter(name=name).exists():
        return JsonResponse({'ok': False, 'error': 'Производитель с таким названием уже существует.'}, status=400)

    old_name = brand.name
    brand.name = name
    brand.save(update_fields=['name'])
    if old_name != name:
        Product.objects.filter(brand=old_name).update(brand=name)

    return JsonResponse({'ok': True, 'brand': _serialize_brand(brand)})


@require_POST
def admin_panel_delete_brand_view(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)
    Product.objects.filter(brand=brand.name).update(brand='')
    brand.delete()
    return JsonResponse({'ok': True})


@require_POST
def admin_panel_update_part_type_view(request, part_type_id):
    category = get_object_or_404(Category.objects.prefetch_related('characteristics_definitions__options'), pk=part_type_id)
    payload = _json_payload(request)
    name = str(payload.get('name') or '').strip()
    characteristics = payload.get('characteristics') or []

    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите тип товара.'}, status=400)

    with transaction.atomic():
        category.name = name
        category.save(update_fields=['name'])
        _replace_part_type_characteristics(category, characteristics)
        category = Category.objects.prefetch_related('characteristics_definitions__options').get(pk=category.pk)

    return JsonResponse({'ok': True, 'part_type': _serialize_part_type(category)})


@require_POST
def admin_panel_delete_part_type_view(request, part_type_id):
    category = get_object_or_404(Category, pk=part_type_id)
    category.delete()
    return JsonResponse({'ok': True})


@require_POST
def admin_panel_update_product_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    is_multipart = 'multipart/form-data' in (request.content_type or '')
    payload = request.POST if is_multipart else _json_payload(request)
    name = str(payload.get('name') or '').strip()
    short_description = str(payload.get('short_description') or '').strip()
    description = str(payload.get('description') or '').strip()
    article = str(payload.get('article') or '').strip()
    vin_number = str(payload.get('vin_number') or '').strip()
    raw_price = payload.get('price')
    raw_stock_quantity = payload.get('stock_quantity')
    brand_id = payload.get('brand_id')
    compatible_vehicles_payload = _parse_product_compatible_vehicles(payload, is_multipart=is_multipart)
    category_id = payload.get('category_id')
    raw_characteristics = (
        _parse_json_string(payload.get('characteristics'), {})
        if is_multipart
        else payload.get('characteristics') or {}
    )
    remove_image_ids = _parse_removed_product_image_ids(payload, is_multipart=is_multipart)
    uploaded_images = list(request.FILES.getlist('images')) if is_multipart else []

    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите название товара.'}, status=400)
    if not category_id:
        return JsonResponse({'ok': False, 'error': 'Выберите тип товара.'}, status=400)
    if not brand_id:
        return JsonResponse({'ok': False, 'error': 'Выберите производителя.'}, status=400)
    try:
        price = _parse_admin_price(raw_price)
    except ValueError as error:
        return JsonResponse({'ok': False, 'error': str(error)}, status=400)
    try:
        stock_quantity = _parse_stock_quantity(raw_stock_quantity)
    except ValueError as error:
        return JsonResponse({'ok': False, 'error': str(error)}, status=400)

    category = get_object_or_404(
        Category.objects.prefetch_related('characteristics_definitions__options'),
        pk=category_id,
    )
    brand = get_object_or_404(Brand, pk=brand_id)
    try:
        compatible_vehicles = _resolve_product_compatible_vehicles(compatible_vehicles_payload)
    except ValueError as error:
        return JsonResponse({'ok': False, 'error': str(error)}, status=400)
    car_brand = compatible_vehicles[0]['car_brand'] if compatible_vehicles else None
    car_model = compatible_vehicles[0]['car_model'] if compatible_vehicles else None
    car_generation = compatible_vehicles[0]['car_generation'] if compatible_vehicles else None
    if car_model and (car_brand is None or car_model.brand_id != car_brand.pk):
        return JsonResponse({'ok': False, 'error': 'Выберите корректную модель автомобиля.'}, status=400)
    if car_generation and (car_model is None or car_generation.model_id != car_model.pk):
        return JsonResponse({'ok': False, 'error': 'Выберите корректное поколение автомобиля.'}, status=400)
    characteristics = _validate_product_characteristics(category, raw_characteristics)

    product.category = category
    product.car_brand = car_brand
    product.car_model = car_model
    product.car_generation = car_generation
    product.brand = brand.name
    product.article = article
    product.vin_number = vin_number
    product.price = price
    product.stock_quantity = stock_quantity
    product.in_stock = stock_quantity > 0
    product.name = name
    product.short_description = short_description
    product.description = description
    product.characteristics = characteristics
    with transaction.atomic():
        product.save(
            update_fields=[
                'category',
                'car_brand',
                'car_model',
                'car_generation',
                'brand',
                'article',
                'vin_number',
                'price',
                'stock_quantity',
                'in_stock',
                'name',
                'short_description',
                'description',
                'characteristics',
                'updated_at',
            ],
        )
        _replace_product_compatible_vehicles(product, compatible_vehicles)
        _replace_product_images(
            product,
            uploaded_images=uploaded_images,
            remove_image_ids=remove_image_ids,
        )

    product = _catalog_queryset().get(pk=product.pk)
    return JsonResponse({'ok': True, 'product': _serialize_admin_product(product)})


@require_POST
def admin_panel_delete_product_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    return JsonResponse({'ok': True})


@require_GET
def admin_panel_users_view(request):
    users = User.objects.prefetch_related(
        Prefetch(
            'order_set',
            queryset=Order.objects.prefetch_related('items').order_by('-created_at'),
            to_attr='admin_orders',
        ),
    ).order_by('username', 'email')
    return JsonResponse({'ok': True, 'users': [_serialize_admin_user(user) for user in users]})


@require_POST
def admin_panel_update_user_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    payload = _json_payload(request)
    username = str(payload.get('name') or '').strip()
    email = str(payload.get('email') or '').strip()
    role = str(payload.get('role') or '').strip()
    orders_payload = payload.get('orders')

    if not username:
        return JsonResponse({'ok': False, 'error': 'Укажите имя пользователя.'}, status=400)
    if not email:
        return JsonResponse({'ok': False, 'error': 'Укажите email пользователя.'}, status=400)
    if role not in {'user', 'admin'}:
        return JsonResponse({'ok': False, 'error': 'Укажите корректную роль пользователя.'}, status=400)
    if User.objects.exclude(pk=user.pk).filter(username=username).exists():
        return JsonResponse({'ok': False, 'error': 'Пользователь с таким именем уже существует.'}, status=400)
    if User.objects.exclude(pk=user.pk).filter(email=email).exists():
        return JsonResponse({'ok': False, 'error': 'Пользователь с таким email уже существует.'}, status=400)

    with transaction.atomic():
        user.username = username
        user.email = email
        user.is_staff = role == 'admin'
        user.is_superuser = role == 'admin'
        user.save(update_fields=['username', 'email', 'is_staff', 'is_superuser'])
        _sync_admin_user_orders(user, orders_payload)

    return JsonResponse({'ok': True, 'user': _serialize_admin_user(user)})


@require_POST
def admin_panel_delete_user_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.user.is_authenticated and request.user.pk == user.pk:
        return JsonResponse({'ok': False, 'error': 'Нельзя удалить текущего пользователя.'}, status=400)
    user.delete()
    return JsonResponse({'ok': True})


@require_http_methods(['GET', 'POST'])
def admin_panel_car_brands_view(request):
    if request.method == 'GET':
        car_brands = CarBrand.objects.prefetch_related('models__generations').order_by('name')
        return JsonResponse({'ok': True, 'car_brands': [_serialize_car_brand(brand) for brand in car_brands]})

    payload = _json_payload(request)
    name = str(payload.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите марку автомобиля.'}, status=400)

    brand, created = CarBrand.objects.get_or_create(name=name)
    return JsonResponse(
        {
            'ok': True,
            'created': created,
            'car_brand': _serialize_car_brand(brand),
        },
    )


@require_POST
def admin_panel_update_car_brand_view(request, car_brand_id):
    brand = get_object_or_404(CarBrand, pk=car_brand_id)
    payload = _json_payload(request)
    name = str(payload.get('name') or '').strip()

    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите марку автомобиля.'}, status=400)
    if CarBrand.objects.exclude(pk=brand.pk).filter(name=name).exists():
        return JsonResponse({'ok': False, 'error': 'Марка автомобиля с таким названием уже существует.'}, status=400)

    brand.name = name
    brand.save(update_fields=['name'])
    brand = CarBrand.objects.prefetch_related('models__generations').get(pk=brand.pk)
    return JsonResponse({'ok': True, 'car_brand': _serialize_car_brand(brand)})


@require_POST
def admin_panel_delete_car_brand_view(request, car_brand_id):
    brand = get_object_or_404(CarBrand, pk=car_brand_id)
    brand.delete()
    return JsonResponse({'ok': True})


@require_POST
def admin_panel_car_models_view(request):
    payload = _json_payload(request)
    brand_id = payload.get('brand_id')
    name = str(payload.get('name') or '').strip()

    if not brand_id:
        return JsonResponse({'ok': False, 'error': 'Выберите марку автомобиля.'}, status=400)
    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите модель автомобиля.'}, status=400)

    brand = get_object_or_404(CarBrand, pk=brand_id)
    car_model, created = CarModel.objects.get_or_create(brand=brand, name=name)
    return JsonResponse(
        {
            'ok': True,
            'created': created,
            'car_model': _serialize_car_model(car_model),
        },
    )


@require_POST
def admin_panel_update_car_model_view(request, car_model_id):
    car_model = get_object_or_404(CarModel.objects.select_related('brand'), pk=car_model_id)
    payload = _json_payload(request)
    brand_id = payload.get('brand_id')
    name = str(payload.get('name') or '').strip()

    if not brand_id:
        return JsonResponse({'ok': False, 'error': 'Выберите марку автомобиля.'}, status=400)
    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите модель автомобиля.'}, status=400)

    brand = get_object_or_404(CarBrand, pk=brand_id)
    if CarModel.objects.exclude(pk=car_model.pk).filter(brand=brand, name=name).exists():
        return JsonResponse({'ok': False, 'error': 'Такая модель уже существует у выбранной марки.'}, status=400)

    car_model.brand = brand
    car_model.name = name
    car_model.save(update_fields=['brand', 'name'])
    car_model = CarModel.objects.select_related('brand').get(pk=car_model.pk)
    return JsonResponse({'ok': True, 'car_model': _serialize_car_model(car_model)})


@require_POST
def admin_panel_delete_car_model_view(request, car_model_id):
    car_model = get_object_or_404(CarModel, pk=car_model_id)
    car_model.delete()
    return JsonResponse({'ok': True})


@require_POST
def admin_panel_car_generations_view(request):
    payload = _json_payload(request)
    brand_id = payload.get('brand_id')
    model_id = payload.get('model_id')
    name = str(payload.get('name') or '').strip()

    if not brand_id:
        return JsonResponse({'ok': False, 'error': 'Выберите марку автомобиля.'}, status=400)
    if not model_id:
        return JsonResponse({'ok': False, 'error': 'Выберите модель автомобиля.'}, status=400)
    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите поколение автомобиля.'}, status=400)

    car_model = get_object_or_404(CarModel.objects.select_related('brand'), pk=model_id)
    if str(car_model.brand_id) != str(brand_id):
        return JsonResponse({'ok': False, 'error': 'Выберите корректную модель для выбранной марки.'}, status=400)

    generation, created = CarGeneration.objects.get_or_create(model=car_model, name=name)
    generation = CarGeneration.objects.select_related('model__brand').get(pk=generation.pk)
    return JsonResponse(
        {
            'ok': True,
            'created': created,
            'car_generation': _serialize_car_generation(generation),
        },
    )


@require_POST
def admin_panel_update_car_generation_view(request, car_generation_id):
    generation = get_object_or_404(CarGeneration.objects.select_related('model__brand'), pk=car_generation_id)
    payload = _json_payload(request)
    brand_id = payload.get('brand_id')
    model_id = payload.get('model_id')
    name = str(payload.get('name') or '').strip()

    if not brand_id:
        return JsonResponse({'ok': False, 'error': 'Выберите марку автомобиля.'}, status=400)
    if not model_id:
        return JsonResponse({'ok': False, 'error': 'Выберите модель автомобиля.'}, status=400)
    if not name:
        return JsonResponse({'ok': False, 'error': 'Укажите поколение автомобиля.'}, status=400)

    car_model = get_object_or_404(CarModel.objects.select_related('brand'), pk=model_id)
    if str(car_model.brand_id) != str(brand_id):
        return JsonResponse({'ok': False, 'error': 'Выберите корректную модель для выбранной марки.'}, status=400)
    if CarGeneration.objects.exclude(pk=generation.pk).filter(model=car_model, name=name).exists():
        return JsonResponse({'ok': False, 'error': 'Такое поколение уже существует у выбранной модели.'}, status=400)

    generation.model = car_model
    generation.name = name
    generation.save(update_fields=['model', 'name'])
    generation = CarGeneration.objects.select_related('model__brand').get(pk=generation.pk)
    return JsonResponse({'ok': True, 'car_generation': _serialize_car_generation(generation)})


@require_POST
def admin_panel_delete_car_generation_view(request, car_generation_id):
    generation = get_object_or_404(CarGeneration, pk=car_generation_id)
    generation.delete()
    return JsonResponse({'ok': True})
