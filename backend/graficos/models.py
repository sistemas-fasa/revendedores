from django.db import models

class FasaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().using('fasa')

class Facturas(models.Model):
    cliente = models.CharField(max_length=5)
    nombre = models.CharField(max_length=45)
    NETO = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    IVA = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    NETO_NETO = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    PRECIO = models.DecimalField(max_digits=13, decimal_places=3, default=0.000)
    UNITARIO = models.DecimalField(max_digits=13, decimal_places=3, default=0.000)
    CANTIDAD = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    FECHA = models.DateField()
    NetoRenglon = models.DecimalField(max_digits=33, decimal_places=11, null=True, blank=True)
    total = models.DecimalField(max_digits=23, decimal_places=7, default=0.0000000)
    PercepcionDGR = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    dgrdetalle = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)
    LOCALIDAD = models.CharField(max_length=4)
    CODIGO = models.CharField(max_length=2, default='F')
    LISTA = models.CharField(max_length=1)
    CLAVE = models.CharField(max_length=8)
    REPARTO = models.CharField(max_length=8)
    COMP = models.CharField(max_length=12, default='0')
    REGIVA = models.CharField(max_length=4)
    IDMOVI = models.IntegerField(default=0)
    CLASE = models.CharField(max_length=1)
    VENDEDOR = models.CharField(max_length=2)
    FLETE = models.DecimalField(max_digits=12, decimal_places=3, default=0.000)
    DESCPRET = models.DecimalField(max_digits=12, decimal_places=3, default=0.000)
    NOTA = models.CharField(max_length=50)
    UNIDAD = models.CharField(max_length=8)
    PAGO = models.CharField(max_length=2, default='00')
    CUOTAPAGO = models.IntegerField(default=1)
    FECHAVEN = models.DateField()
    FECHA1VENC = models.DateField()
    fletetransp = models.DecimalField(max_digits=12, decimal_places=3, default=0.000)
    boni = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    COSTO = models.DecimalField(max_digits=12, decimal_places=3, default=0.000)
    Introduccion = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    SUCURSAL = models.ForeignKey('Sucursales', on_delete=models.CASCADE, db_column='SUCURSAL')
    CONTADO = models.CharField(max_length=1, default='S')
    IDSTOCKVE = models.IntegerField(default=0)
    DETEXT = models.TextField(null=True, blank=True)
    aliciva = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    DESCAD = models.CharField(max_length=40)
    Procesado = models.BooleanField(default=False)
    PAGOANT = models.BooleanField(default=False)
    Item = models.CharField(max_length=3)
    GastoTar = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)
    DES1 = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    PUNITORIO = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    REPARTE = models.CharField(max_length=1)

    objects = FasaManager()

    class Meta:
        db_table = 'facturas'
        managed = False
        app_label = 'graficos'
        default_manager_name = 'objects'

    def save(self, *args, **kwargs):
        kwargs['using'] = 'fasa'
        super().save(*args, **kwargs)

class Sucursales(models.Model):
    id_sucursal = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=40)
    direccion = models.CharField(max_length=80)

    objects = FasaManager()
    
    class Meta:
        db_table = 'sucursales'
        managed = False        
        
class Grupos(models.Model):
    codigo = models.CharField(max_length=4, primary_key=True)
    nombre = models.CharField(max_length=30, null=True, blank=True)

    objects = FasaManager()
    
    class Meta:
        db_table = 'grupos'
        managed = False
