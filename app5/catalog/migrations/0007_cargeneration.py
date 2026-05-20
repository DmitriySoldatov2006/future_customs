from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_product_car_brand_product_car_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarGeneration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generations', to='catalog.carmodel')),
            ],
            options={
                'verbose_name': 'Car generation',
                'verbose_name_plural': 'Car generations',
                'ordering': ['model__brand__name', 'model__name', 'name'],
            },
        ),
        migrations.AddConstraint(
            model_name='cargeneration',
            constraint=models.UniqueConstraint(fields=('model', 'name'), name='unique_car_generation_per_model'),
        ),
    ]
