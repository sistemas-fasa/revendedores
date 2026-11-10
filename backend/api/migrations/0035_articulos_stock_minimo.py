# Generated for stock semáforo: mínimo por rotación + vínculo padre/hijo.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0034_articulodestacado'),
    ]

    operations = [
        migrations.AddField(
            model_name='articulos',
            name='descuenta_de',
            field=models.CharField(blank=True, default='', max_length=8, verbose_name='Descuenta Stock De'),
        ),
        migrations.AddField(
            model_name='articulos',
            name='stock_minimo',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=12, null=True, verbose_name='Stock Mínimo'),
        ),
    ]
