from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_product_brand_product_vin_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Brand',
                'verbose_name_plural': 'Brands',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='article',
            field=models.CharField(blank=True, max_length=255, verbose_name='Article'),
        ),
        migrations.AddField(
            model_name='product',
            name='characteristics',
            field=models.JSONField(blank=True, default=dict, verbose_name='Characteristics'),
        ),
        migrations.CreateModel(
            name='CategoryCharacteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('key', models.SlugField(max_length=255)),
                ('allows_custom_value', models.BooleanField(default=False)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='characteristics_definitions', to='catalog.category')),
            ],
            options={
                'verbose_name': 'Category characteristic',
                'verbose_name_plural': 'Category characteristics',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='CategoryCharacteristicOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('characteristic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='catalog.categorycharacteristic')),
            ],
            options={
                'verbose_name': 'Characteristic option',
                'verbose_name_plural': 'Characteristic options',
                'ordering': ['sort_order', 'value'],
            },
        ),
        migrations.AddConstraint(
            model_name='categorycharacteristic',
            constraint=models.UniqueConstraint(fields=('category', 'key'), name='unique_category_characteristic_key'),
        ),
    ]
