# Reglas de ocultamiento de artículos en la web (exacta/prefijo).
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0037_clave_ampliada_12'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticuloOculto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('exacta', 'Clave exacta'), ('prefijo', 'Prefijo')], default='exacta', max_length=7)),
                ('patron', models.CharField(max_length=12, verbose_name='Clave o prefijo')),
                ('motivo', models.CharField(blank=True, default='', max_length=100)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='ocultos_creados', to='auth.user')),
            ],
            options={
                'verbose_name': 'Artículo oculto',
                'verbose_name_plural': 'Artículos ocultos',
                'ordering': ['tipo', 'patron'],
            },
        ),
        migrations.AddConstraint(
            model_name='articulooculto',
            constraint=models.UniqueConstraint(fields=('tipo', 'patron'), name='oculto_tipo_patron_unico'),
        ),
    ]
