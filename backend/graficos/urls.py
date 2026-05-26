from django.urls import path
from .views import FacturasGraficoAPIView, SucursalesListAPIView

urlpatterns = [
    path('facturas-grafico/', FacturasGraficoAPIView.as_view(), name='facturas-grafico'),
    path('sucursales/', SucursalesListAPIView.as_view(), name='sucursales-list'),
]
