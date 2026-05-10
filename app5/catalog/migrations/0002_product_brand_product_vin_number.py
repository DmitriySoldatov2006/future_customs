from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, max_length=255, verbose_name='Бренд'),
        ),
        migrations.AddField(
            model_name='product',
            name='vin_number',
            field=models.CharField(blank=True, max_length=64, verbose_name='VIN номер'),
        ),
    ]
