from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_product_compatibilities(apps, schema_editor):
    Product = apps.get_model('catalog', 'Product')
    ProductCompatibleVehicle = apps.get_model('catalog', 'ProductCompatibleVehicle')

    for product in Product.objects.exclude(car_brand__isnull=True).iterator():
        ProductCompatibleVehicle.objects.get_or_create(
            product_id=product.pk,
            car_brand_id=product.car_brand_id,
            car_model_id=product.car_model_id,
            car_generation_id=product.car_generation_id,
            defaults={'sort_order': 0},
        )


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_product_stock_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCompatibleVehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('car_brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_compatibilities', to='catalog.carbrand')),
                ('car_generation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_compatibilities', to='catalog.cargeneration')),
                ('car_model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_compatibilities', to='catalog.carmodel')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compatible_vehicles', to='catalog.product')),
            ],
            options={
                'verbose_name': 'Product compatible vehicle',
                'verbose_name_plural': 'Product compatible vehicles',
                'ordering': ['sort_order', 'pk'],
            },
        ),
        migrations.AddConstraint(
            model_name='productcompatiblevehicle',
            constraint=models.UniqueConstraint(fields=('product', 'car_brand', 'car_model', 'car_generation'), name='unique_product_compatible_vehicle'),
        ),
        migrations.RunPython(migrate_existing_product_compatibilities, noop_reverse),
    ]
