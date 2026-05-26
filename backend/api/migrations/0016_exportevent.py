from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_alter_articulos_clave_alter_cliente_numero_cliente_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExportEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('favoritos', 'Exportar Favoritos'), ('carrito', 'Exportar Carrito'), ('otros', 'Otros')], default='favoritos', max_length=50)),
                ('parametros', models.JSONField(blank=True, null=True, help_text='Parámetros usados para la exportación (modalidad, con_impuestos, etc.)')),
                ('total_items', models.IntegerField(default=0, help_text='Cantidad de items incluidos en la exportación')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('fecha_hora', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='export_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Evento de Exportación',
                'verbose_name_plural': 'Eventos de Exportación',
                'ordering': ['-fecha_hora'],
            },
        ),
    ]
