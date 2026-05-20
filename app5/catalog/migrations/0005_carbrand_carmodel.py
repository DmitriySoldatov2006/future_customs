from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_productimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarBrand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Car brand',
                'verbose_name_plural': 'Car brands',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CarModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='models', to='catalog.carbrand')),
            ],
            options={
                'verbose_name': 'Car model',
                'verbose_name_plural': 'Car models',
                'ordering': ['brand__name', 'name'],
            },
        ),
        migrations.AddConstraint(
            model_name='carmodel',
            constraint=models.UniqueConstraint(fields=('brand', 'name'), name='unique_car_model_per_brand'),
        ),
    ]
