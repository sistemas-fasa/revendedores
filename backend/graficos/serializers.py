from rest_framework import serializers
from .models import Facturas, Sucursales

class FacturaGraficoSerializer(serializers.Serializer):
    periodo = serializers.CharField()
    retira = serializers.DecimalField(max_digits=33, decimal_places=11)
    reparto = serializers.DecimalField(max_digits=33, decimal_places=11)
    total = serializers.DecimalField(max_digits=33, decimal_places=11)

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursales
        fields = ['id_sucursal', 'nombre']
