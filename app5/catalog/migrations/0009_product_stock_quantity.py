from django.db import migrations, models


def seed_stock_quantity(apps, schema_editor):
    Product = apps.get_model('catalog', 'Product')
    Product.objects.filter(in_stock=True).update(stock_quantity=1)
    Product.objects.filter(in_stock=False).update(stock_quantity=0)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_product_car_generation'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(default=1, verbose_name='Stock quantity'),
        ),
        migrations.RunPython(seed_stock_quantity, migrations.RunPython.noop),
    ]
