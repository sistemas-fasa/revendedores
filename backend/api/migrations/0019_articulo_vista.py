from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_pedido_modalidad_con_impuestos'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticuloVista',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('oferta', 'Oferta'), ('discontinuado', 'Discontinuado')], max_length=20)),
                ('fecha_hora', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.cliente')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articulos_vistos', to='auth.user')),
            ],
            options={
                'verbose_name': 'Vista de Articulo (Oferta/Discontinuado)',
                'verbose_name_plural': 'Vistas de Articulos (Oferta/Discontinuado)',
                'ordering': ['-fecha_hora'],
            },
        ),
    ]
