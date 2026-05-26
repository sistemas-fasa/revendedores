from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_cobranzas_cuentacorrientecliente_factura'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='modalidad',
            field=models.CharField(choices=[('retira', 'Retira'), ('reparto', 'Reparto')], default='retira', max_length=10),
        ),
        migrations.AddField(
            model_name='pedido',
            name='con_impuestos',
            field=models.BooleanField(default=True),
        ),
    ]
