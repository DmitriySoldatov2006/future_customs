from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_carbrand_carmodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='car_brand',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='catalog.carbrand'),
        ),
        migrations.AddField(
            model_name='product',
            name='car_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='catalog.carmodel'),
        ),
    ]
