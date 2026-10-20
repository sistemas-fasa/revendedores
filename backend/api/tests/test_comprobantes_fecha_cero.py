"""
Regresión de las fechas cero del ERP legacy ('0000-00-00').

El ERP (VFP) exporta la cuenta corriente a MySQL usando '0000-00-00' como
centinela de "sin fecha de vencimiento". pymysql devuelve esos valores DATE
inválidos como texto y el backend MySQL de Django no los convierte, así que
el string llegaba intacto al atributo del modelo y `fechaven.strftime(...)`
reventaba con:

    AttributeError: 'str' object has no attribute 'strftime'

y /api/comprobantes/ respondía HTTP 500. Afectaba a 3.535 clientes (8.435 de
1.265.574 comprobantes); el cliente 00591 era uno de ellos.

Además, como en MySQL '0000-00-00' ordena antes que cualquier fecha real, un
filtro `fechaven < hoy` contaba esos comprobantes como "deuda vencida" en el
dashboard aunque no tengan vencimiento.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import connection, models
from django.test import SimpleTestCase, TransactionTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from api.fechas import ZERO_DATE, FechaContableField, esta_vencido, formatear_fecha, normalizar_fecha
from api.models import Cliente, FormaPago, Localidades
from api.views import comprobantes_cliente, dashboard_kpis, detalle_comprobante


class CuentaCorrienteStub(models.Model):
    """Replica de la vista `cuenta_corriente_clientes`.

    Las columnas de vencimiento van como texto para poder guardar el
    centinela '0000-00-00' tal cual lo entrega MySQL.
    """

    id = models.AutoField(primary_key=True)
    cliente = models.CharField(max_length=5)
    nombre = models.CharField(max_length=45)
    neto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha = models.DateField()
    fechaven = models.CharField(max_length=10, null=True, blank=True)
    fecha1venc = models.CharField(max_length=10, null=True, blank=True)
    pago = models.CharField(max_length=2, default="00")
    forma_pago = models.CharField(max_length=40, null=True, blank=True)
    codigo = models.CharField(max_length=1)
    clase = models.CharField(max_length=1, default="B")
    numero = models.CharField(max_length=12, default="0")

    class Meta:
        app_label = "api"
        db_table = "cuenta_corriente_stub"
        ordering = ["-fecha", "-numero"]


class CuentaCorrienteFechaRealStub(models.Model):
    """Igual que `CuentaCorrienteStub` pero con el campo contable real.

    Sirve para comprobar que el lookup `con_fecha_valida` se aplica en el SQL.
    Los agregados no seleccionan la columna de fecha, así que no interfiere con
    el conversor de fechas de SQLite.
    """

    id = models.AutoField(primary_key=True)
    cliente = models.CharField(max_length=5)
    nombre = models.CharField(max_length=45)
    neto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha = models.DateField()
    fechaven = FechaContableField()
    fecha1venc = FechaContableField()
    pago = models.CharField(max_length=2, default="00")
    forma_pago = models.CharField(max_length=40, null=True, blank=True)
    codigo = models.CharField(max_length=1)
    clase = models.CharField(max_length=1, default="B")
    numero = models.CharField(max_length=12, default="0")

    class Meta:
        app_label = "api"
        db_table = "cuenta_corriente_fecha_real_stub"
        ordering = ["-fecha", "-numero"]


class CobranzasStub(models.Model):
    """Replica minima de la vista `cobranzas` para el detalle de recibos."""

    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=1, null=True, blank=True)
    recibo = models.CharField(max_length=12, null=True, blank=True)
    codigo = models.CharField(max_length=1, null=True, blank=True)
    clase = models.CharField(max_length=1, null=True, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    detalle = models.CharField(max_length=40, null=True, blank=True)
    banco = models.CharField(max_length=20, null=True, blank=True)
    numero = models.CharField(max_length=12, null=True, blank=True)
    vence = models.CharField(max_length=10, null=True, blank=True)
    impentra = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)
    comp = models.CharField(max_length=12, null=True, blank=True)

    class Meta:
        app_label = "api"
        db_table = "cobranzas_stub"


class NormalizacionFechaERPTests(SimpleTestCase):
    """El centinela '0000-00-00' se interpreta como 'sin fecha'."""

    def test_fecha_cero_se_convierte_en_none(self):
        campo = FechaContableField()
        self.assertIsNone(campo.from_db_value(ZERO_DATE, None, None))

    def test_fecha_valida_se_conserva(self):
        campo = FechaContableField()
        self.assertEqual(campo.from_db_value("2026-10-14", None, None), date(2026, 10, 14))

    def test_fecha_ya_convertida_se_conserva(self):
        campo = FechaContableField()
        self.assertEqual(campo.from_db_value(date(2026, 10, 14), None, None), date(2026, 10, 14))

    def test_none_se_conserva(self):
        campo = FechaContableField()
        self.assertIsNone(campo.from_db_value(None, None, None))

    def test_fecha_imposible_se_convierte_en_none(self):
        campo = FechaContableField()
        self.assertIsNone(campo.from_db_value("2026-02-31", None, None))

    def test_normalizar_fecha_acepta_el_centinela_del_erp(self):
        self.assertIsNone(normalizar_fecha(ZERO_DATE))
        self.assertEqual(normalizar_fecha("2026-10-14"), date(2026, 10, 14))
        self.assertIsNone(normalizar_fecha(None))
        self.assertIsNone(normalizar_fecha(""))

    def test_formatear_fecha_devuelve_texto_iso_o_none(self):
        self.assertEqual(formatear_fecha(date(2026, 10, 14)), "2026-10-14")
        self.assertEqual(formatear_fecha("2026-10-14"), "2026-10-14")
        self.assertIsNone(formatear_fecha(ZERO_DATE))
        self.assertIsNone(formatear_fecha(None))

    def test_sin_vencimiento_no_esta_vencido(self):
        class Comprobante:
            fechaven = ZERO_DATE
            saldo = Decimal("3600000.00")

        self.assertFalse(esta_vencido(Comprobante(), hoy=date(2026, 10, 19)))

    def test_con_vencimiento_anterior_y_saldo_esta_vencido(self):
        class Comprobante:
            fechaven = date(2026, 10, 1)
            saldo = Decimal("100.00")

        self.assertTrue(esta_vencido(Comprobante(), hoy=date(2026, 10, 19)))

    def test_sin_saldo_no_esta_vencido(self):
        class Comprobante:
            fechaven = date(2026, 10, 1)
            saldo = Decimal("0.00")

        self.assertFalse(esta_vencido(Comprobante(), hoy=date(2026, 10, 19)))


class ComprobantesFechaCeroTests(TransactionTestCase):
    """Los comprobantes con fecha cero del ERP no pueden romper la API.

    Va de `TransactionTestCase` (y no de `TestCase`) porque las tablas de las
    réplicas se crean a mano y MySQL no permite DDL dentro de una transacción.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._crear_tablas()

    @classmethod
    def tearDownClass(cls):
        cls._borrar_tablas()
        super().tearDownClass()

    @staticmethod
    def _crear_tablas():
        existentes = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for modelo in (CuentaCorrienteStub, CuentaCorrienteFechaRealStub, CobranzasStub):
                if modelo._meta.db_table not in existentes:
                    editor.create_model(modelo)

    @staticmethod
    def _borrar_tablas():
        existentes = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for modelo in (CuentaCorrienteFechaRealStub, CobranzasStub, CuentaCorrienteStub):
                if modelo._meta.db_table in existentes:
                    editor.delete_model(modelo)

    def setUp(self):
        self.user = User.objects.create_user(username="cliente591", password="test")
        self.forma_pago = FormaPago.objects.create(
            id="00",
            nombre="Contado",
            lista="1",
            descuento=Decimal("10.00"),
            punitorio=Decimal("0.00"),
        )
        self.localidad = Localidades.objects.create(
            codigo="0001",
            nombre="Posadas",
            distancia=0,
            fletep1=Decimal("5.00"),
            fletetn1=Decimal("1000.00"),
            fletep4=Decimal("8.00"),
            fletetn4=Decimal("1500.00"),
            reparto="S",
        )
        self.cliente = Cliente.objects.create(
            user=self.user,
            numero_cliente="00591",
            lista_precio="1",
            nombre="Cliente con fecha cero",
            codigo_localidad=self.localidad,
            condicion_pago=self.forma_pago,
            tipo_responsable_iva="C",
        )

    def _request(self, url, **params):
        request = APIRequestFactory().get(url, params)
        force_authenticate(request, user=self.user)
        return request

    def _crear_comprobante(self, **kwargs):
        defaults = {
            "cliente": "00591",
            "nombre": "Cliente con fecha cero",
            "neto": Decimal("100.00"),
            "total": Decimal("121.00"),
            "saldo": Decimal("0.00"),
            "fecha": date(2026, 10, 14),
            "fechaven": ZERO_DATE,
            "fecha1venc": ZERO_DATE,
            "pago": "00",
            "forma_pago": "CONTADO",
            "codigo": "C",
            "clase": "A",
            "numero": "999999999902",
        }
        defaults.update(kwargs)
        return CuentaCorrienteStub.objects.create(**defaults)

    def test_lista_de_comprobantes_no_falla_con_fecha_cero(self):
        """Regresión del cliente 00591: la lista devolvía HTTP 500."""
        self._crear_comprobante()

        with patch("api.models.CuentaCorrienteCliente", CuentaCorrienteStub):
            response = comprobantes_cliente(self._request("/api/comprobantes/"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)

        comprobante = response.data["data"][0]
        self.assertIsNone(comprobante["fecha_vencimiento"])
        self.assertIsNone(comprobante["fecha_primer_vencimiento"])
        self.assertEqual(comprobante["fecha"], "2026-10-14")
        self.assertEqual(comprobante["estado"], "Vigente")

    def test_lista_conserva_las_fechas_validas(self):
        self._crear_comprobante(
            numero="002000019151",
            codigo="F",
            fechaven="2026-11-07",
            fecha1venc="2026-10-31",
        )

        with patch("api.models.CuentaCorrienteCliente", CuentaCorrienteStub):
            response = comprobantes_cliente(self._request("/api/comprobantes/"))

        self.assertEqual(response.status_code, 200)
        comprobante = response.data["data"][0]
        self.assertEqual(comprobante["fecha_vencimiento"], "2026-11-07")
        self.assertEqual(comprobante["fecha_primer_vencimiento"], "2026-10-31")
        self.assertEqual(comprobante["tipo_comprobante"], "Factura")

    def test_comprobante_vencido_con_fecha_valida(self):
        self._crear_comprobante(
            numero="001900061525",
            codigo="F",
            saldo=Decimal("1000.00"),
            fechaven="2026-10-01",
            fecha1venc="2026-10-01",
        )

        with patch("api.models.CuentaCorrienteCliente", CuentaCorrienteStub):
            response = comprobantes_cliente(self._request("/api/comprobantes/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"][0]["estado"], "Vencido")

    def test_detalle_de_recibo_con_fecha_cero(self):
        self._crear_comprobante(
            numero="000100171753",
            codigo="R",
            saldo=Decimal("0.00"),
            fechaven="2026-10-14",
            fecha1venc="2026-10-14",
        )
        CobranzasStub.objects.create(
            tipo="C",
            recibo="000100171753",
            monto=Decimal("500.00"),
            detalle="Pago de prueba",
            banco="Galicia",
            numero="123",
            vence=ZERO_DATE,
            impentra=Decimal("0.00"),
            comp="000100171753",
        )

        with patch("api.models.CuentaCorrienteCliente", CuentaCorrienteStub), \
                patch("api.models.Cobranzas", CobranzasStub):
            response = detalle_comprobante(
                self._request("/api/comprobantes/000100171753/"), "000100171753"
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["data"]["items"][0]["vence"])
        self.assertEqual(response.data["data"]["encabezado"]["fecha"], "2026-10-14")

    def _crear_comprobante_fecha_real(self, **kwargs):
        """Inserta por SQL crudo, que es como llega la fecha cero del ERP.

        Django no deja guardar '0000-00-00' en un DateField (no es una fecha
        válida), y el ERP lo escribe directo en la base.
        """
        defaults = {
            "cliente": "00591",
            "nombre": "Cliente con fecha cero",
            "neto": "0.00",
            "total": "0.00",
            "saldo": "0.00",
            "fecha": "2026-10-14",
            "fechaven": ZERO_DATE,
            "fecha1venc": ZERO_DATE,
            "pago": "00",
            "forma_pago": "CONTADO",
            "codigo": "E",
            "clase": "A",
            "numero": "000100002662",
        }
        defaults.update(kwargs)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO cuenta_corriente_fecha_real_stub "
                "(cliente, nombre, neto, total, saldo, fecha, fechaven, fecha1venc, "
                " pago, forma_pago, codigo, clase, numero) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    defaults["cliente"],
                    defaults["nombre"],
                    defaults["neto"],
                    defaults["total"],
                    defaults["saldo"],
                    defaults["fecha"],
                    defaults["fechaven"],
                    defaults["fecha1venc"],
                    defaults["pago"],
                    defaults["forma_pago"],
                    defaults["codigo"],
                    defaults["clase"],
                    defaults["numero"],
                ],
            )

    def test_dashboard_no_cuenta_la_fecha_cero_como_deuda_vencida(self):
        """'0000-00-00' ordena antes que hoy: sin el filtro, era deuda vencida."""
        self._crear_comprobante_fecha_real(
            saldo="3600000.00",
            numero="000100002662",
        )
        self._crear_comprobante_fecha_real(
            neto="100.00",
            total="121.00",
            saldo="1000.00",
            fecha="2026-10-01",
            fechaven="2026-10-01",
            fecha1venc="2026-10-01",
            codigo="F",
            numero="001900061525",
        )

        with patch("api.models.CuentaCorrienteCliente", CuentaCorrienteFechaRealStub):
            response = dashboard_kpis(self._request("/api/dashboard/kpis/"))

        self.assertEqual(response.status_code, 200)
        kpis = response.data["data"]
        self.assertEqual(float(kpis["deuda_vencida"]), 1000.00)
        self.assertEqual(float(kpis["deuda_por_vencer"]), 0.00)
        self.assertEqual(float(kpis["saldo_total"]), 3601000.00)
