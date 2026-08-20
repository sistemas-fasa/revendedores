from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_bot_conversation_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='cliente_snapshot',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='pedido',
            name='condicion_pago',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pedidos',
                to='api.formapago',
            ),
        ),
    ]
