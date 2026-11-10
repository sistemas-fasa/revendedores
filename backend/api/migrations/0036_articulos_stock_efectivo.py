# Generated for stock semáforo: efectivo calculado por el actualizador horario.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0035_articulos_stock_minimo'),
    ]

    operations = [
        migrations.AddField(
            model_name='articulos',
            name='stock_efectivo',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=12, null=True, verbose_name='Stock Efectivo'),
        ),
    ]
