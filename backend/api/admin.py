from django.contrib import admin
from .models import BonificacionCliente, Cliente, FormaPago, Localidades, Articulos, ExportEvent, LinkOpen

# Register your models here.

class ArticulosAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'unidad', 'precio1', 'precio4', 'stock')
    search_fields = ('nombre',) # Add search by name
    list_filter = ('grupo',)

class LocalidadesAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'distancia')
    search_fields = ('nombre',)

class BonificacionClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'desde_articulo', 'hasta_articulo', 'bonificacion')
    search_fields = ('cliente__nombre', 'desde_articulo', 'hasta_articulo')
    list_filter = ('cliente',)
    raw_id_fields = ('cliente',)

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_localidad', 'lista_precio')
    search_fields = ('nombre',)
    list_filter = ('lista_precio',)
    raw_id_fields = ('codigo_localidad','user')

admin.site.register(Cliente, ClienteAdmin)
    
admin.site.register(FormaPago)
admin.site.register(Localidades, LocalidadesAdmin)
admin.site.register(Articulos, ArticulosAdmin)
admin.site.register(BonificacionCliente, BonificacionClienteAdmin)


class ExportEventAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'total_items', 'fecha_hora', 'ip_address')
    search_fields = ('usuario__username', 'tipo')
    list_filter = ('tipo', 'fecha_hora')

admin.site.register(ExportEvent, ExportEventAdmin)


class LinkOpenAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'campaign', 'target_url', 'ip_address', 'opened_at')
    search_fields = ('recipient_email', 'campaign')
    list_filter = ('campaign', 'opened_at')


admin.site.register(LinkOpen, LinkOpenAdmin)
