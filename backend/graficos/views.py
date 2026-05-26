
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q, F, Value, CharField, Case, When, DecimalField
from django.db.models.functions import TruncMonth
from .models import Facturas, Sucursales
from .serializers import FacturaGraficoSerializer, SucursalSerializer
from datetime import datetime

class FacturasGraficoAPIView(APIView):
	permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
	
	def get(self, request):
		print(f"Parámetros recibidos: {dict(request.GET)}")
		
		# Filtros
		articulo_min = request.GET.get('articulo_min', '')
		articulo_max = request.GET.get('articulo_max', '')
		reparto = request.GET.get('reparto', 'todos')  # 'retira', 'reparto', 'todos'
		sucursal = request.GET.get('sucursal')
		fecha_desde = request.GET.get('fecha_desde')
		fecha_hasta = request.GET.get('fecha_hasta')
		pagoant = request.GET.get('pagoant')  # 'si', 'no', 'todos'

		qs = Facturas.objects.all()
		print(f"Registros totales antes de filtros: {qs.count()}")

		# Verificar algunos registros de muestra
		sample_records = qs.values('FECHA', 'CLAVE', 'REPARTO', 'NetoRenglon', 'SUCURSAL_id')[:5]
		print(f"Muestra de registros: {list(sample_records)}")

		# Verificar registros con NetoRenglon > 0
		records_with_neto = qs.filter(NetoRenglon__gt=0).count()
		print(f"Registros con NetoRenglon > 0: {records_with_neto}")

		# Filtro de artículos (por CLAVE) - solo si se proporcionan valores
		if articulo_min and articulo_max:
			qs = qs.filter(CLAVE__gte=articulo_min, CLAVE__lte=articulo_max)
			print(f"Después de filtro artículos ({articulo_min} - {articulo_max}): {qs.count()}")
		elif articulo_min:
			qs = qs.filter(CLAVE__gte=articulo_min)
			print(f"Después de filtro artículo mínimo ({articulo_min}): {qs.count()}")
		elif articulo_max:
			qs = qs.filter(CLAVE__lte=articulo_max)
			print(f"Después de filtro artículo máximo ({articulo_max}): {qs.count()}")

		# Filtro de reparto/retira
		if reparto == 'retira':
			qs = qs.filter(REPARTO__iexact='N')
			print(f"Después de filtro retira: {qs.count()}")
		elif reparto == 'reparto':
			qs = qs.filter(REPARTO__iexact='S')
			print(f"Después de filtro reparto: {qs.count()}")
		# else: todos

		# Filtro de sucursal
		if sucursal:
			qs = qs.filter(SUCURSAL__id_sucursal=sucursal)
			print(f"Después de filtro sucursal ({sucursal}): {qs.count()}")

		# Filtro de fechas
		if fecha_desde:
			qs = qs.filter(FECHA__gte=fecha_desde)
			print(f"Después de filtro fecha desde ({fecha_desde}): {qs.count()}")
		if fecha_hasta:
			qs = qs.filter(FECHA__lte=fecha_hasta)
			print(f"Después de filtro fecha hasta ({fecha_hasta}): {qs.count()}")

		# Filtro de pago anticipado
		if pagoant == 'si':
			qs = qs.filter(PAGOANT=True)
			print(f"Después de filtro pago anticipado SI: {qs.count()}")
		elif pagoant == 'no':
			qs = qs.filter(PAGOANT=False)
			print(f"Después de filtro pago anticipado NO: {qs.count()}")
		# else: todos

		print(f"Registros finales después de todos los filtros: {qs.count()}")

		# Agrupar por periodo (mes) y agregar sumas condicionales
		data = qs.annotate(
			periodo=TruncMonth('FECHA')
		).values('periodo').annotate(
			retira=Sum(
				Case(
					When(REPARTO__iexact='N', then='NetoRenglon'),
					default=Value(0),
					output_field=DecimalField(max_digits=33, decimal_places=11)
				)
			),
			reparto=Sum(
				Case(
					When(REPARTO__iexact='S', then='NetoRenglon'),
					default=Value(0),
					output_field=DecimalField(max_digits=33, decimal_places=11)
				)
			),
			total=Sum('NetoRenglon')
		).order_by('periodo')

		print(f"Query SQL: {data.query}")
		print(f"Datos agrupados: {list(data)}")
		
		# Formatear los datos para el serializer
		formatted_data = []
		for item in data:
			formatted_data.append({
				'periodo': item['periodo'].strftime('%Y-%m'),
				'retira': float(item['retira'] or 0),
				'reparto': float(item['reparto'] or 0),
				'total': float(item['total'] or 0)
			})

		print(f"Datos formateados: {formatted_data}")
		serializer = FacturaGraficoSerializer(formatted_data, many=True)
		return Response(serializer.data)


class SucursalesListAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request):
        try:
            print("Intentando obtener sucursales...")
            sucursales = Sucursales.objects.all()
            print(f"Sucursales encontradas: {sucursales.count()}")
            serializer = SucursalSerializer(sucursales, many=True)
            print(f"Datos serializados: {serializer.data}")
            return Response(serializer.data)
        except Exception as e:
            print(f"Error al obtener sucursales: {str(e)}")
            return Response({'error': str(e)}, status=500)