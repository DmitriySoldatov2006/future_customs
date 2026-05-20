from decimal import Decimal, InvalidOperation

from django.db import models


class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    car_brand = models.ForeignKey(
        'CarBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    car_model = models.ForeignKey(
        'CarModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    car_generation = models.ForeignKey(
        'CarGeneration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    brand = models.CharField(max_length=255, blank=True, verbose_name='Brand')
    article = models.CharField(max_length=255, blank=True, verbose_name='Article')
    vin_number = models.CharField(max_length=64, blank=True, verbose_name='VIN')
    name = models.CharField(max_length=255, verbose_name='Name')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    short_description = models.CharField(max_length=500, blank=True, verbose_name='Short description')
    description = models.TextField(blank=True, verbose_name='Description')
    characteristics = models.JSONField(default=dict, blank=True, verbose_name='Characteristics')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    stock_quantity = models.PositiveIntegerField(default=1, verbose_name='Stock quantity')
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Old price',
    )
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Image')
    in_stock = models.BooleanField(default=True, verbose_name='In stock')
    is_featured = models.BooleanField(default=False, verbose_name='Featured')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('product_detail', kwargs={'slug': self.slug})

    @property
    def discount_percent(self):
        if not self.old_price:
            return None
        try:
            price = Decimal(str(self.price))
            old_price = Decimal(str(self.old_price))
        except (InvalidOperation, TypeError, ValueError):
            return None
        if old_price > price:
            return int((1 - price / old_price) * 100)
        return None


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='products/', verbose_name='Image')
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'pk']
        verbose_name = 'Product image'
        verbose_name_plural = 'Product images'

    def __str__(self):
        return f'{self.product.name} image {self.pk}'


class ProductCompatibleVehicle(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='compatible_vehicles',
    )
    car_brand = models.ForeignKey(
        'CarBrand',
        on_delete=models.CASCADE,
        related_name='product_compatibilities',
    )
    car_model = models.ForeignKey(
        'CarModel',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='product_compatibilities',
    )
    car_generation = models.ForeignKey(
        'CarGeneration',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='product_compatibilities',
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'pk']
        verbose_name = 'Product compatible vehicle'
        verbose_name_plural = 'Product compatible vehicles'
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'car_brand', 'car_model', 'car_generation'],
                name='unique_product_compatible_vehicle',
            ),
        ]

    def __str__(self):
        parts = [
            self.car_brand.name if self.car_brand_id else '',
            self.car_model.name if self.car_model_id else '',
            self.car_generation.name if self.car_generation_id else '',
        ]
        label = ' '.join(part.strip() for part in parts if part).strip()
        return f'{self.product.name}: {label or "compatibility"}'


class CarBrand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Car brand'
        verbose_name_plural = 'Car brands'

    def __str__(self):
        return self.name


class CarModel(models.Model):
    brand = models.ForeignKey(
        CarBrand,
        on_delete=models.CASCADE,
        related_name='models',
    )
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['brand__name', 'name']
        verbose_name = 'Car model'
        verbose_name_plural = 'Car models'
        constraints = [
            models.UniqueConstraint(
                fields=['brand', 'name'],
                name='unique_car_model_per_brand',
            ),
        ]

    def __str__(self):
        return f'{self.brand.name} {self.name}'


class CarGeneration(models.Model):
    model = models.ForeignKey(
        CarModel,
        on_delete=models.CASCADE,
        related_name='generations',
    )
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['model__brand__name', 'model__name', 'name']
        verbose_name = 'Car generation'
        verbose_name_plural = 'Car generations'
        constraints = [
            models.UniqueConstraint(
                fields=['model', 'name'],
                name='unique_car_generation_per_model',
            ),
        ]

    def __str__(self):
        return f'{self.model.brand.name} {self.model.name} {self.name}'


class CategoryCharacteristic(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='characteristics_definitions',
    )
    name = models.CharField(max_length=255)
    key = models.SlugField(max_length=255)
    allows_custom_value = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Category characteristic'
        verbose_name_plural = 'Category characteristics'
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'key'],
                name='unique_category_characteristic_key',
            ),
        ]

    def __str__(self):
        return f'{self.category}: {self.name}'


class CategoryCharacteristicOption(models.Model):
    characteristic = models.ForeignKey(
        CategoryCharacteristic,
        on_delete=models.CASCADE,
        related_name='options',
    )
    value = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'value']
        verbose_name = 'Characteristic option'
        verbose_name_plural = 'Characteristic options'

    def __str__(self):
        return self.value
