# Código ampliado ERP: claves de 9 (y futuras) dejaban afuera artículos nuevos.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0036_articulos_stock_efectivo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articulos',
            name='clave',
            field=models.CharField(max_length=12, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='articulos',
            name='unidad',
            field=models.CharField(max_length=12),
        ),
        migrations.AlterField(
            model_name='articulos',
            name='descuenta_de',
            field=models.CharField(blank=True, default='', max_length=12, verbose_name='Descuenta Stock De'),
        ),
        migrations.AlterField(
            model_name='bonificacioncliente',
            name='desde_articulo',
            field=models.CharField(max_length=12, verbose_name='Desde Artículo'),
        ),
        migrations.AlterField(
            model_name='bonificacioncliente',
            name='hasta_articulo',
            field=models.CharField(max_length=12, verbose_name='Hasta Artículo'),
        ),
    ]
