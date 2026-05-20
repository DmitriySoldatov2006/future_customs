import json
import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings

from cart.cart import serialize_product
from checkout.models import Order, OrderItem

from .models import Brand, CarBrand, CarGeneration, CarModel, Category, CategoryCharacteristic, CategoryCharacteristicOption, Product, ProductCompatibleVehicle, ProductImage


class CatalogViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Тормоза',
            slug='brakes',
        )
        self.car_brand = CarBrand.objects.create(name='BMW')
        self.car_model = CarModel.objects.create(brand=self.car_brand, name='X5')
        self.car_generation = CarGeneration.objects.create(model=self.car_model, name='G05')
        self.product = Product.objects.create(
            category=self.category,
            car_brand=self.car_brand,
            car_model=self.car_model,
            car_generation=self.car_generation,
            brand='Brembo',
            vin_number='WBA5A7C50GG123456',
            name='Тормозные колодки передние',
            slug='front-brake-pads',
            short_description='Керамические колодки для передней оси',
            description='ABS комплект для спортивного торможения',
            price='4990.00',
            stock_quantity=5,
            old_price='5790.00',
            in_stock=True,
        )

    def test_serialize_product_includes_part_number_and_derived_characteristics(self):
        payload = serialize_product(self.product, quantity=2)

        self.assertEqual(payload['part_number'], 'FRONT-BRAKE-PADS')
        self.assertEqual(payload['article'], 'WBA5A7C50GG123456')
        self.assertEqual(payload['quantity'], 2)
        self.assertTrue(payload['in_cart'])
        self.assertEqual(payload['stock_quantity'], 5)
        self.assertTrue(payload['is_available'])
        self.assertEqual(payload['car_brand_name'], 'BMW')
        self.assertEqual(payload['car_model_name'], 'X5')
        self.assertEqual(payload['car_generation_name'], 'G05')
        self.assertEqual(payload['compatible_vehicle'], 'BMW X5 G05')
        self.assertIn('vin_number', payload['characteristics'])
        self.assertIn('material', payload['characteristics'])
        self.assertIn('placement', payload['characteristics'])

    def test_serialize_product_includes_multiple_compatible_vehicles(self):
        next_brand = CarBrand.objects.create(name='Audi')
        next_model = CarModel.objects.create(brand=next_brand, name='A6')
        next_generation = CarGeneration.objects.create(model=next_model, name='C8')
        ProductCompatibleVehicle.objects.create(
            product=self.product,
            car_brand=self.car_brand,
            car_model=self.car_model,
            car_generation=self.car_generation,
            sort_order=0,
        )
        ProductCompatibleVehicle.objects.create(
            product=self.product,
            car_brand=next_brand,
            car_model=next_model,
            car_generation=next_generation,
            sort_order=1,
        )

        payload = serialize_product(Product.objects.prefetch_related('compatible_vehicles__car_brand', 'compatible_vehicles__car_model', 'compatible_vehicles__car_generation').get(pk=self.product.pk))

        self.assertEqual(len(payload['compatible_vehicles']), 2)
        self.assertEqual(payload['compatible_vehicles'][0]['label'], 'BMW X5 G05')
        self.assertEqual(payload['compatible_vehicles'][1]['label'], 'Audi A6 C8')
        self.assertEqual(payload['compatible_vehicle'], 'BMW X5 G05, Audi A6 C8')

    def test_catalog_view_uses_session_cart_state_for_product_cards(self):
        session = self.client.session
        session['cart'] = {
            str(self.product.pk): {
                'quantity': 2,
                'price_snapshot': '4990.00',
            }
        }
        session.save()

        response = self.client.get(reverse('catalog'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results_count'], 1)
        serialized = response.context['products'][0]
        self.assertEqual(serialized['quantity'], 2)
        self.assertTrue(serialized['in_cart'])
        self.assertContains(response, 'data-product-id="{}"'.format(self.product.pk))
        self.assertContains(response, 'data-cart-count')
        self.assertEqual(
            response.context['part_type_options'],
            [{'value': 'brakes', 'label': self.category.name}],
        )
        self.assertEqual(
            response.context['brand_options'],
            [{'value': 'Brembo', 'label': 'Brembo'}],
        )

    def test_catalog_view_shows_out_of_stock_products_with_ended_status(self):
        Product.objects.create(
            category=self.category,
            brand='ATE',
            name='Товар вне наличия',
            slug='out-of-stock-item',
            short_description='Скрытый товар',
            price='1990.00',
            stock_quantity=0,
            in_stock=False,
        )

        response = self.client.get(reverse('catalog'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results_count'], 2)
        self.assertEqual(len(response.context['products']), 2)
        out_of_stock_product = next(item for item in response.context['products'] if item['slug'] == 'out-of-stock-item')
        self.assertEqual(out_of_stock_product['stock_label'], 'Закончилось')


class AdminPanelTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(lambda: shutil.rmtree(self.media_root, ignore_errors=True))

        self.brand = Brand.objects.create(name='Bosch')
        self.category = Category.objects.create(name='Sensors', slug='sensors')
        self.custom_characteristic = CategoryCharacteristic.objects.create(
            category=self.category,
            name='Compatibility',
            key='compatibility',
            allows_custom_value=True,
            sort_order=0,
        )
        self.choice_characteristic = CategoryCharacteristic.objects.create(
            category=self.category,
            name='Voltage',
            key='voltage',
            allows_custom_value=False,
            sort_order=1,
        )
        CategoryCharacteristicOption.objects.create(
            characteristic=self.choice_characteristic,
            value='12V',
            sort_order=0,
        )
        CategoryCharacteristicOption.objects.create(
            characteristic=self.choice_characteristic,
            value='24V',
            sort_order=1,
        )
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='secret123',
        )
        self.admin_user = User.objects.create_superuser(
            username='root',
            email='root@example.com',
            password='secret123',
        )

    def test_admin_panel_page_renders_context(self):
        response = self.client.get(reverse('admin_panel'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/admin_panel.html')
        self.assertEqual(response.context['admin_panel_brands'][0]['name'], 'Bosch')
        self.assertEqual(response.context['admin_panel_part_types'][0]['slug'], 'sensors')
        self.assertEqual(response.context['admin_panel_car_brands'], [])

    def test_create_brand_endpoint_creates_brand(self):
        response = self.client.post(
            reverse('admin_panel_create_brand'),
            data=json.dumps({'name': 'ATE'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Brand.objects.filter(name='ATE').exists())
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['brand']['name'], 'ATE')

    def test_create_part_type_endpoint_creates_characteristics_and_options(self):
        response = self.client.post(
            reverse('admin_panel_create_part_type'),
            data=json.dumps(
                {
                    'name': 'Brake pads',
                    'characteristics': [
                        {
                            'name': 'Material',
                            'values': [
                                {'value': 'Ceramic', 'is_custom': False},
                                {'value': 'Semi-metallic', 'is_custom': False},
                            ],
                        },
                        {
                            'name': 'Placement',
                            'values': [
                                {'value': '', 'is_custom': True},
                            ],
                        },
                    ],
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        category = Category.objects.get(slug='brake-pads')
        material = CategoryCharacteristic.objects.get(category=category, key='material')
        placement = CategoryCharacteristic.objects.get(category=category, key='placement')

        self.assertFalse(material.allows_custom_value)
        self.assertTrue(placement.allows_custom_value)
        self.assertEqual(
            list(material.options.values_list('value', flat=True)),
            ['Ceramic', 'Semi-metallic'],
        )
        self.assertFalse(placement.options.exists())

        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['part_type']['slug'], 'brake-pads')
        self.assertEqual(len(payload['part_type']['characteristics']), 2)

    def test_create_product_endpoint_saves_validated_characteristics(self):
        response = self.client.post(
            reverse('admin_panel_create_product'),
            data=json.dumps(
                {
                    'name': 'Oxygen sensor',
                    'short_description': 'Front sensor',
                    'description': 'OEM replacement sensor',
                    'article': 'OS-100',
                    'vin_number': 'VIN123',
                    'price': '14990',
                    'stock_quantity': 7,
                    'brand_id': self.brand.pk,
                    'category_id': self.category.pk,
                    'characteristics': {
                        'compatibility': 'BMW E90',
                        'voltage': '12V',
                        'unknown': 'ignored',
                        'voltage_invalid': 'ignored',
                    },
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(slug='os-100')

        self.assertEqual(product.brand, 'Bosch')
        self.assertEqual(
            product.characteristics,
            {
                'compatibility': 'BMW E90',
                'voltage': '12V',
            },
        )
        self.assertEqual(str(product.price), '14990.00')
        self.assertEqual(product.stock_quantity, 7)
        self.assertTrue(product.in_stock)

        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['product']['name'], 'Oxygen sensor')

    def test_create_product_endpoint_saves_multiple_compatible_vehicles(self):
        bmw = CarBrand.objects.create(name='BMW')
        x5 = CarModel.objects.create(brand=bmw, name='X5')
        g05 = CarGeneration.objects.create(model=x5, name='G05')
        audi = CarBrand.objects.create(name='Audi')
        a6 = CarModel.objects.create(brand=audi, name='A6')
        c8 = CarGeneration.objects.create(model=a6, name='C8')

        response = self.client.post(
            reverse('admin_panel_create_product'),
            data=json.dumps(
                {
                    'name': 'Control arm',
                    'description': 'Compatibility list check',
                    'article': 'ARM-100',
                    'price': '11990',
                    'stock_quantity': 3,
                    'brand_id': self.brand.pk,
                    'category_id': self.category.pk,
                    'compatible_vehicles': [
                        {
                            'car_brand_id': bmw.pk,
                            'car_model_id': x5.pk,
                            'car_generation_id': g05.pk,
                        },
                        {
                            'car_brand_id': audi.pk,
                            'car_model_id': a6.pk,
                            'car_generation_id': c8.pk,
                        },
                    ],
                    'characteristics': {
                        'compatibility': 'Multiple vehicles',
                    },
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(slug='arm-100')
        compatible_vehicles = list(product.compatible_vehicles.order_by('sort_order'))

        self.assertEqual(len(compatible_vehicles), 2)
        self.assertEqual(product.car_brand, bmw)
        self.assertEqual(product.car_model, x5)
        self.assertEqual(product.car_generation, g05)
        self.assertEqual(compatible_vehicles[1].car_brand, audi)
        self.assertEqual(compatible_vehicles[1].car_model, a6)
        self.assertEqual(compatible_vehicles[1].car_generation, c8)

    def test_create_product_endpoint_saves_multiple_uploaded_images(self):
        car_brand = CarBrand.objects.create(name='BMW')
        car_model = CarModel.objects.create(brand=car_brand, name='X5')
        car_generation = CarGeneration.objects.create(model=car_model, name='G05')

        response = self.client.post(
            reverse('admin_panel_create_product'),
            data={
                'name': 'Camera kit',
                'short_description': 'Front and rear camera set',
                'description': 'Set of two cameras for the product gallery',
                'article': 'CAM-200',
                'vin_number': 'VIN999',
                'price': '25990.50',
                'stock_quantity': '4',
                'brand_id': str(self.brand.pk),
                'car_brand_id': str(car_brand.pk),
                'car_model_id': str(car_model.pk),
                'car_generation_id': str(car_generation.pk),
                'category_id': str(self.category.pk),
                'characteristics': json.dumps(
                    {
                        'compatibility': 'Universal',
                        'voltage': '24V',
                    },
                ),
                'images': [
                    SimpleUploadedFile('front.jpg', b'front-image-content', content_type='image/jpeg'),
                    SimpleUploadedFile('rear.jpg', b'rear-image-content', content_type='image/jpeg'),
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(slug='cam-200')
        product_images = list(product.images.order_by('sort_order'))

        self.assertEqual(len(product_images), 2)
        self.assertTrue(product.image.name.endswith('front.jpg'))
        self.assertEqual(product_images[0].image.name, product.image.name)
        self.assertEqual(product.car_brand, car_brand)
        self.assertEqual(product.car_model, car_model)
        self.assertEqual(product.car_generation, car_generation)
        self.assertEqual(str(product.price), '25990.50')
        self.assertEqual(product.stock_quantity, 4)
        self.assertEqual(
            list(ProductImage.objects.filter(product=product).values_list('sort_order', flat=True)),
            [0, 1],
        )

        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['product']['images_count'], 2)

    def test_get_products_endpoint_returns_all_products(self):
        Product.objects.create(
            category=self.category,
            brand='Bosch',
            article='PS-10',
            vin_number='VIN-PS-10',
            name='Pressure sensor',
            slug='pressure-sensor',
            short_description='Works in fuel systems',
            description='Detailed product description',
            characteristics={'voltage': '12V'},
            price='0.00',
            stock_quantity=3,
            in_stock=True,
        )

        response = self.client.get(reverse('admin_panel_create_product'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(len(payload['products']), 1)
        self.assertEqual(payload['products'][0]['name'], 'Pressure sensor')
        self.assertEqual(payload['products'][0]['category_name'], 'Sensors')
        self.assertEqual(payload['products'][0]['stock_quantity'], 3)

    def test_update_part_type_endpoint_replaces_characteristics(self):
        response = self.client.post(
            reverse('admin_panel_update_part_type', args=[self.category.pk]),
            data=json.dumps(
                {
                    'name': 'Updated sensors',
                    'characteristics': [
                        {
                            'name': 'Connector',
                            'values': [
                                {'value': '3-pin', 'is_custom': False},
                                {'value': '4-pin', 'is_custom': False},
                            ],
                        },
                    ],
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated sensors')
        self.assertFalse(self.category.characteristics_definitions.filter(key='compatibility').exists())
        connector = self.category.characteristics_definitions.get(key='connector')
        self.assertEqual(list(connector.options.values_list('value', flat=True)), ['3-pin', '4-pin'])

    def test_update_brand_endpoint_renames_existing_products_brand(self):
        product = Product.objects.create(
            category=self.category,
            brand='Bosch',
            article='OS-10',
            name='Old brand product',
            slug='old-brand-product',
            short_description='Short description',
            description='Long description',
            price='0.00',
            stock_quantity=5,
            in_stock=True,
        )

        response = self.client.post(
            reverse('admin_panel_update_brand', args=[self.brand.pk]),
            data=json.dumps({'name': 'Bosch Pro'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.brand.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual(self.brand.name, 'Bosch Pro')
        self.assertEqual(product.brand, 'Bosch Pro')

    def test_update_product_endpoint_updates_fields_and_characteristics(self):
        car_brand = CarBrand.objects.create(name='Audi')
        car_model = CarModel.objects.create(brand=car_brand, name='A6')
        car_generation = CarGeneration.objects.create(model=car_model, name='C8')

        product = Product.objects.create(
            category=self.category,
            car_brand=car_brand,
            car_model=car_model,
            car_generation=car_generation,
            brand='Bosch',
            article='OS-100',
            vin_number='VIN123',
            name='Oxygen sensor',
            slug='oxygen-sensor',
            short_description='Front sensor',
            description='OEM replacement sensor',
            characteristics={'compatibility': 'BMW E90', 'voltage': '12V'},
            price='0.00',
            stock_quantity=6,
            in_stock=True,
        )

        new_category = Category.objects.create(name='Modules', slug='modules')
        module_characteristic = CategoryCharacteristic.objects.create(
            category=new_category,
            name='Generation',
            key='generation',
            allows_custom_value=False,
            sort_order=0,
        )
        CategoryCharacteristicOption.objects.create(
            characteristic=module_characteristic,
            value='Gen 2',
            sort_order=0,
        )

        next_car_brand = CarBrand.objects.create(name='BMW')
        next_car_model = CarModel.objects.create(brand=next_car_brand, name='X5')
        next_car_generation = CarGeneration.objects.create(model=next_car_model, name='G05')

        response = self.client.post(
            reverse('admin_panel_update_product', args=[product.pk]),
            data=json.dumps(
                {
                    'name': 'Updated sensor',
                    'short_description': 'Updated short description',
                    'description': 'Updated long description',
                    'article': 'UPD-100',
                    'vin_number': 'VIN-UPDATED',
                    'price': '18990.25',
                    'stock_quantity': 2,
                    'brand_id': self.brand.pk,
                    'car_brand_id': next_car_brand.pk,
                    'car_model_id': next_car_model.pk,
                    'car_generation_id': next_car_generation.pk,
                    'category_id': new_category.pk,
                    'characteristics': {'generation': 'Gen 2', 'compatibility': 'ignored'},
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Updated sensor')
        self.assertEqual(product.category, new_category)
        self.assertEqual(product.car_brand, next_car_brand)
        self.assertEqual(product.car_model, next_car_model)
        self.assertEqual(product.car_generation, next_car_generation)
        self.assertEqual(str(product.price), '18990.25')
        self.assertEqual(product.stock_quantity, 2)
        self.assertEqual(product.characteristics, {'generation': 'Gen 2'})

    def test_update_product_endpoint_replaces_multiple_compatible_vehicles(self):
        audi = CarBrand.objects.create(name='Audi')
        a6 = CarModel.objects.create(brand=audi, name='A6')
        c8 = CarGeneration.objects.create(model=a6, name='C8')
        bmw = CarBrand.objects.create(name='BMW')
        x5 = CarModel.objects.create(brand=bmw, name='X5')
        g05 = CarGeneration.objects.create(model=x5, name='G05')

        product = Product.objects.create(
            category=self.category,
            car_brand=audi,
            car_model=a6,
            car_generation=c8,
            brand='Bosch',
            article='LINK-100',
            name='Stabilizer link',
            slug='stabilizer-link',
            description='Test product',
            price='0.00',
            stock_quantity=1,
            in_stock=True,
        )
        ProductCompatibleVehicle.objects.create(
            product=product,
            car_brand=audi,
            car_model=a6,
            car_generation=c8,
            sort_order=0,
        )

        response = self.client.post(
            reverse('admin_panel_update_product', args=[product.pk]),
            data=json.dumps(
                {
                    'name': 'Updated stabilizer link',
                    'description': 'Updated',
                    'article': 'LINK-200',
                    'price': '9990',
                    'stock_quantity': 5,
                    'brand_id': self.brand.pk,
                    'category_id': self.category.pk,
                    'compatible_vehicles': [
                        {
                            'car_brand_id': bmw.pk,
                            'car_model_id': x5.pk,
                            'car_generation_id': g05.pk,
                        },
                    ],
                    'characteristics': {},
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        compatible_vehicles = list(product.compatible_vehicles.order_by('sort_order'))
        self.assertEqual(len(compatible_vehicles), 1)
        self.assertEqual(product.car_brand, bmw)
        self.assertEqual(product.car_model, x5)
        self.assertEqual(product.car_generation, g05)
        self.assertEqual(compatible_vehicles[0].car_generation, g05)

    def test_update_product_endpoint_allows_deleting_and_uploading_images(self):
        product = Product.objects.create(
            category=self.category,
            brand='Bosch',
            article='IMG-100',
            name='Image test product',
            slug='image-test-product',
            description='Test product',
            characteristics={'voltage': '12V'},
            price='0.00',
            stock_quantity=2,
            in_stock=True,
        )
        first_image = ProductImage.objects.create(
            product=product,
            image=SimpleUploadedFile('first.jpg', b'first-image-content', content_type='image/jpeg'),
            sort_order=0,
        )
        second_image = ProductImage.objects.create(
            product=product,
            image=SimpleUploadedFile('second.jpg', b'second-image-content', content_type='image/jpeg'),
            sort_order=1,
        )
        product.image = first_image.image.name
        product.save(update_fields=['image'])

        response = self.client.post(
            reverse('admin_panel_update_product', args=[product.pk]),
            data={
                'name': 'Image test product',
                'description': 'Updated image set',
                'article': 'IMG-100',
                'vin_number': '',
                'price': '1250',
                'stock_quantity': '3',
                'brand_id': str(self.brand.pk),
                'category_id': str(self.category.pk),
                'compatible_vehicles': json.dumps([]),
                'characteristics': json.dumps({'voltage': '12V'}),
                'remove_image_ids': json.dumps([first_image.pk]),
                'images': [
                    SimpleUploadedFile('third.jpg', b'third-image-content', content_type='image/jpeg'),
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        product_images = list(product.images.order_by('sort_order', 'pk'))

        self.assertEqual(len(product_images), 2)
        self.assertNotIn(first_image.pk, [image.pk for image in product_images])
        self.assertTrue(any(image.image.name.endswith('third.jpg') for image in product_images))
        self.assertEqual(product.image.name, product_images[0].image.name)

        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(len(payload['product']['images']), 2)

    def test_users_endpoint_lists_and_updates_role(self):
        order = Order.objects.create(
            user=self.user,
            full_name='Manager User',
            phone='+79990000000',
            region='Moscow region',
            city='Moscow',
            address='Lenina 1',
            total='14990.00',
            status='new',
        )
        OrderItem.objects.create(
            order=order,
            product_id='front-brake-pads',
            name='Brake pads',
            quantity=2,
            price='7495.00',
        )
        removed_order = Order.objects.create(
            user=self.user,
            full_name='Old Manager User',
            phone='+78880000000',
            region='Old region',
            city='Old city',
            address='Old address 1',
            total='5000.00',
            status='new',
        )
        OrderItem.objects.create(
            order=removed_order,
            product_id='legacy-item',
            name='Legacy item',
            quantity=1,
            price='5000.00',
        )

        response = self.client.get(reverse('admin_panel_users'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['users'][0]['role'], 'user')
        self.assertEqual(payload['users'][0]['orders'][0]['status'], 'new')

        update_response = self.client.post(
            reverse('admin_panel_update_user', args=[self.user.pk]),
            data=json.dumps(
                {
                    'name': 'manager-updated',
                    'email': 'manager-updated@example.com',
                    'role': 'admin',
                    'orders': [
                        {
                            'id': order.pk,
                            'full_name': 'Updated Manager User',
                            'phone': '+79991112233',
                            'region': 'Saint Petersburg',
                            'city': 'Saint Petersburg',
                            'address': 'Nevsky 10',
                            'total': '9900.00',
                            'status': 'completed',
                            'items': [
                                {
                                    'id': order.items.first().pk,
                                    'product_id': 'front-brake-pads',
                                    'name': 'Updated Brake pads',
                                    'quantity': 1,
                                    'price': '9900.00',
                                },
                            ],
                        },
                    ],
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(update_response.status_code, 200)
        self.user.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.user.username, 'manager-updated')
        self.assertEqual(self.user.email, 'manager-updated@example.com')
        self.assertTrue(self.user.is_superuser)
        self.assertTrue(self.user.is_staff)
        self.assertEqual(order.full_name, 'Updated Manager User')
        self.assertEqual(order.phone, '+79991112233')
        self.assertEqual(order.region, 'Saint Petersburg')
        self.assertEqual(order.city, 'Saint Petersburg')
        self.assertEqual(order.address, 'Nevsky 10')
        self.assertEqual(str(order.total), '9900.00')
        self.assertEqual(order.status, 'completed')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().name, 'Updated Brake pads')
        self.assertFalse(Order.objects.filter(pk=removed_order.pk).exists())

    def test_update_user_allows_deleting_all_orders(self):
        order = Order.objects.create(
            user=self.user,
            full_name='Manager User',
            phone='+79990000000',
            region='Moscow region',
            city='Moscow',
            address='Lenina 1',
            total='14990.00',
            status='new',
        )
        OrderItem.objects.create(
            order=order,
            product_id='front-brake-pads',
            name='Brake pads',
            quantity=2,
            price='7495.00',
        )

        response = self.client.post(
            reverse('admin_panel_update_user', args=[self.user.pk]),
            data=json.dumps(
                {
                    'name': 'manager',
                    'email': 'manager@example.com',
                    'role': 'user',
                    'orders': [],
                },
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.filter(pk=order.pk).exists())

    def test_create_car_brand_endpoint_creates_brand_and_lists_it(self):
        response = self.client.post(
            reverse('admin_panel_car_brands'),
            data=json.dumps({'name': 'BMW'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(CarBrand.objects.filter(name='BMW').exists())
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['car_brand']['name'], 'BMW')

        list_response = self.client.get(reverse('admin_panel_car_brands'))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()['car_brands'][0]['name'], 'BMW')

    def test_create_car_model_endpoint_creates_model_for_brand(self):
        car_brand = CarBrand.objects.create(name='Audi')

        response = self.client.post(
            reverse('admin_panel_car_models'),
            data=json.dumps({'brand_id': car_brand.pk, 'name': 'A6'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(CarModel.objects.filter(brand=car_brand, name='A6').exists())
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['car_model']['brand_name'], 'Audi')

    def test_update_car_brand_endpoint_renames_brand(self):
        car_brand = CarBrand.objects.create(name='Audi')

        response = self.client.post(
            reverse('admin_panel_update_car_brand', args=[car_brand.pk]),
            data=json.dumps({'name': 'Audi Sport'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        car_brand.refresh_from_db()
        self.assertEqual(car_brand.name, 'Audi Sport')
        self.assertEqual(response.json()['car_brand']['name'], 'Audi Sport')

    def test_update_car_model_endpoint_changes_name_and_brand(self):
        audi = CarBrand.objects.create(name='Audi')
        bmw = CarBrand.objects.create(name='BMW')
        car_model = CarModel.objects.create(brand=audi, name='A6')

        response = self.client.post(
            reverse('admin_panel_update_car_model', args=[car_model.pk]),
            data=json.dumps({'brand_id': bmw.pk, 'name': 'X5'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        car_model.refresh_from_db()
        self.assertEqual(car_model.brand, bmw)
        self.assertEqual(car_model.name, 'X5')
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['car_model']['brand_name'], 'BMW')

    def test_create_car_generation_endpoint_creates_generation_for_model(self):
        car_brand = CarBrand.objects.create(name='Audi')
        car_model = CarModel.objects.create(brand=car_brand, name='A6')

        response = self.client.post(
            reverse('admin_panel_car_generations'),
            data=json.dumps({'brand_id': car_brand.pk, 'model_id': car_model.pk, 'name': 'C8'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(CarGeneration.objects.filter(model=car_model, name='C8').exists())
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['car_generation']['model_name'], 'A6')
        self.assertEqual(payload['car_generation']['brand_name'], 'Audi')

    def test_update_car_generation_endpoint_changes_name_and_model(self):
        audi = CarBrand.objects.create(name='Audi')
        bmw = CarBrand.objects.create(name='BMW')
        audi_model = CarModel.objects.create(brand=audi, name='A6')
        bmw_model = CarModel.objects.create(brand=bmw, name='X5')
        generation = CarGeneration.objects.create(model=audi_model, name='C8')

        response = self.client.post(
            reverse('admin_panel_update_car_generation', args=[generation.pk]),
            data=json.dumps({'brand_id': bmw.pk, 'model_id': bmw_model.pk, 'name': 'G05'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        generation.refresh_from_db()
        self.assertEqual(generation.model, bmw_model)
        self.assertEqual(generation.name, 'G05')

    def test_delete_car_generation_endpoint_removes_generation(self):
        car_brand = CarBrand.objects.create(name='Audi')
        car_model = CarModel.objects.create(brand=car_brand, name='A6')
        generation = CarGeneration.objects.create(model=car_model, name='C8')

        response = self.client.post(
            reverse('admin_panel_delete_car_generation', args=[generation.pk]),
            data=json.dumps({}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CarGeneration.objects.filter(pk=generation.pk).exists())

    def test_delete_car_model_endpoint_removes_model(self):
        car_brand = CarBrand.objects.create(name='Audi')
        car_model = CarModel.objects.create(brand=car_brand, name='A6')

        response = self.client.post(
            reverse('admin_panel_delete_car_model', args=[car_model.pk]),
            data=json.dumps({}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CarModel.objects.filter(pk=car_model.pk).exists())
