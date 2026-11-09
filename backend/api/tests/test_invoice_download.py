import io
import json
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from api.services.erp_documents import ReceiptApplicationMismatch, download_receipt_pdf
from api.views import descargar_comprobante_pdf


class InvoiceDownloadTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)
        self.customer = type("Customer", (), {"numero_cliente": "00591"})()
        self.pdf = b"%PDF-1.4 synthetic"
        self.erp_response = io.BytesIO(self.pdf)
        self.erp_response.status = 200
        self.erp_response.headers = {"Content-Type": "application/pdf"}

    def _get(self, tipo="F", numero="000100000001", authenticated=True):
        request = self.factory.get(f"/api/comprobantes/{tipo}/{numero}/pdf/")
        if authenticated:
            force_authenticate(request, user=self.user)
        return descargar_comprobante_pdf(request, tipo, numero)

    @override_settings(
        EMPRESA_ID=2,
        ACCOUNTING_DB_ALIAS="default",
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.views.Cliente.objects.get")
    @patch("api.services.erp_documents.CuentaCorrienteCliente.objects.using")
    @patch("api.services.erp_documents.urlopen")
    def test_descarga_pdf_autenticada_con_referencia_comercial_y_headers_privados(
        self, urlopen, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.count.return_value = 1
        urlopen.return_value.__enter__.return_value = self.erp_response

        response = self._get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response["Cache-Control"].startswith("private, no-store"))
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(response.content, self.pdf)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer integration-secret")
        self.assertNotIn(b"idmovi", request.data)
        self.assertNotIn(b"integration-secret", response.content)
        self.assertEqual(
            json.loads(request.data),
            {
                "company_id": 2,
                "customer_code": "00591",
                "document_type": "F",
                "invoice_number": "000100000001",
            },
        )
        customer_get.assert_called_once_with(user=self.user)
        account_using.assert_called_once_with("default")

    @override_settings(
        EMPRESA_ID=2,
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.views.Cliente.objects.get")
    @patch("api.services.erp_documents.CuentaCorrienteCliente.objects.using")
    @patch("api.services.erp_documents.urlopen")
    def test_no_consulta_erp_si_el_comprobante_no_pertenece_al_cliente(
        self, urlopen, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.count.return_value = 0

        response = self._get()

        self.assertEqual(response.status_code, 404)
        urlopen.assert_not_called()

    def test_requiere_jwt(self):
        request = self.factory.get("/api/comprobantes/F/000100000001/pdf/")
        response = descargar_comprobante_pdf(request, "F", "000100000001")
        self.assertEqual(response.status_code, 401)

    @override_settings(
        EMPRESA_ID=2,
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.views.Cliente.objects.get")
    @patch("api.services.erp_documents.CuentaCorrienteCliente.objects.using")
    @patch("api.services.erp_documents.urlopen")
    def test_erp_fiscalmente_rechazado_se_devuelve_como_error_seguro(
        self, urlopen, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.count.return_value = 1
        urlopen.side_effect = HTTPError("https://erp.example", 422, "invalid fiscal data", {}, None)

        response = self._get()

        self.assertEqual(response.status_code, 422)
        self.assertNotIn("invalid fiscal data", str(response.data))

    @override_settings(
        EMPRESA_ID=2,
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.views.Cliente.objects.get")
    @patch("api.services.erp_documents.CuentaCorrienteCliente.objects.using")
    @patch("api.services.erp_documents.urlopen")
    def test_erp_no_disponible_se_devuelve_como_503(
        self, urlopen, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.count.return_value = 1
        urlopen.side_effect = URLError("internal integration secret")

        response = self._get()

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("internal integration secret", str(response.data))

    @override_settings(
        EMPRESA_ID=2,
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.views.Cliente.objects.get")
    @patch("api.services.erp_documents.CuentaCorrienteCliente.objects.using")
    @patch("api.services.erp_documents.urlopen")
    def test_rechaza_referencias_ambiguas_sin_consultar_al_erp(
        self, urlopen, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.count.return_value = 2

        response = self._get()

        self.assertEqual(response.status_code, 404)
        urlopen.assert_not_called()

    @override_settings(
        EMPRESA_ID=2,
        ERP_DOCUMENT_RENDER_URL="",
        ERP_DOCUMENT_API_TOKEN="",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.views.Cliente.objects.get")
    @patch("api.services.erp_documents.CuentaCorrienteCliente.objects.using")
    @patch("api.services.erp_documents.urlopen")
    def test_falla_con_mensaje_seguro_si_la_integracion_no_esta_configurada(
        self, urlopen, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.count.return_value = 1

        response = self._get()

        self.assertEqual(response.status_code, 503)
        urlopen.assert_not_called()

    @override_settings(
        EMPRESA_ID=2,
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.views.Cliente.objects.get")
    @patch("api.services.erp_documents.CuentaCorrienteCliente.objects.using")
    @patch("api.services.erp_documents.urlopen")
    def test_erp_404_por_cliente_o_empresa_no_expone_que_existe_el_comprobante(
        self, urlopen, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.count.return_value = 1
        urlopen.side_effect = HTTPError("https://erp.example", 404, "private data", {}, None)

        response = self._get()

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("private data", str(response.data))

    @override_settings(EMPRESA_ID=2, ACCOUNTING_DB_ALIAS="default")
    @patch("api.views.Cliente.objects.get")
    @patch("api.models.CuentaCorrienteCliente.objects.using")
    @patch("api.models.Cobranzas.objects.using")
    @patch("api.views.connections")
    @patch("api.views.download_receipt_pdf")
    def test_recibo_autenticado_envia_medios_de_pago_al_renderizador(
        self, download_pdf, connections_mock, payments_using, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.exists.return_value = True
        payment = SimpleNamespace(
            monto=1250, tipo="R", codigo="F", detalle="Transferencia",
            banco="Banco", numero="ref-1", vence=None,
        )
        payments_using.return_value.filter.return_value.order_by.return_value = [payment]
        connections_mock.__getitem__.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = []
        download_pdf.return_value = self.pdf

        response = self._get(tipo="R", numero="000100000001")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("recibo-R-000100000001.pdf", response["Content-Disposition"])
        self.assertEqual(
            download_pdf.call_args.kwargs["payments"],
            [{
                "amount": "1250.00",
                "method": "R · F · Transferencia",
                "bank": "Banco",
                "reference": "ref-1",
                "due_date": None,
            }],
        )

    @override_settings(EMPRESA_ID=2, ACCOUNTING_DB_ALIAS="default")
    @patch("api.views.Cliente.objects.get")
    @patch("api.models.CuentaCorrienteCliente.objects.using")
    @patch("api.views.download_receipt_pdf")
    def test_recibo_ajeno_no_se_envia_al_renderizador(self, download_pdf, account_using, customer_get):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.exists.return_value = False

        response = self._get(tipo="R", numero="000100000001")

        self.assertEqual(response.status_code, 404)
        download_pdf.assert_not_called()

    @override_settings(EMPRESA_ID=2, ACCOUNTING_DB_ALIAS="default")
    @patch("api.views.Cliente.objects.get")
    @patch("api.models.CuentaCorrienteCliente.objects.using")
    @patch("api.models.Cobranzas.objects.using")
    @patch("api.views.connections")
    @patch("api.views.download_receipt_pdf", side_effect=ReceiptApplicationMismatch)
    def test_recibo_inconsistente_devuelve_mensaje_de_aplicaciones(self, download_pdf, connections_mock, payments_using, account_using, customer_get):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.exists.return_value = True
        payments_using.return_value.filter.return_value.order_by.return_value = []
        connections_mock.__getitem__.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = []

        response = self._get(tipo="R", numero="000100000001")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["message"], "El recibo no coincide con las facturas aplicadas.")

    @override_settings(EMPRESA_ID=2, ACCOUNTING_DB_ALIAS="default")
    @patch("api.views.Cliente.objects.get")
    @patch("api.models.CuentaCorrienteCliente.objects.using")
    @patch("api.models.Cobranzas.objects.using")
    @patch("api.views.connections")
    @patch("api.views.download_receipt_pdf")
    def test_recibo_a_cuenta_envia_medios_de_caja_al_renderizador(
        self, download_pdf, connections_mock, payments_using, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.exists.return_value = True
        payments_using.return_value.filter.return_value.order_by.return_value = []
        cursor = connections_mock.__getitem__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("12", "Dep. Cta. HARTGE JOSE NOLI", "", "", "2026-11-03", 2000000.00, "DEPOSITO EN CUENTA"),
            ("03", "Cobranza", "CORRIENTES S.A.", "31343291", "2026-10-26", 403333.33, "CHEQUE TERCERO"),
        ]
        download_pdf.return_value = self.pdf

        response = self._get(tipo="R", numero="000300018948")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            download_pdf.call_args.kwargs["payments"],
            [
                {
                    "amount": "2000000.00",
                    "method": "DEPOSITO EN CUENTA · Dep. Cta. HARTGE JOSE NOLI",
                    "bank": None,
                    "reference": None,
                    "due_date": "2026-11-03",
                },
                {
                    "amount": "403333.33",
                    "method": "CHEQUE TERCERO · Cobranza",
                    "bank": "CORRIENTES S.A.",
                    "reference": "31343291",
                    "due_date": "2026-10-26",
                },
            ],
        )
        self.assertEqual(
            download_pdf.call_args.kwargs["valores"],
            download_pdf.call_args.kwargs["payments"],
        )

    @override_settings(EMPRESA_ID=2, ACCOUNTING_DB_ALIAS="default")
    @patch("api.views.Cliente.objects.get")
    @patch("api.models.CuentaCorrienteCliente.objects.using")
    @patch("api.models.Cobranzas.objects.using")
    @patch("api.views.connections")
    @patch("api.views.download_receipt_pdf")
    def test_recibo_solo_compensado_usa_caja_y_no_duplica_aplicaciones(
        self, download_pdf, connections_mock, payments_using, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.exists.return_value = True
        linked = SimpleNamespace(
            monto=2403333.33, tipo="R", codigo="R", detalle="Cobranza",
            banco="", numero="", vence=None,
        )
        payments_using.return_value.filter.return_value.order_by.return_value = [linked]
        cursor = connections_mock.__getitem__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("12", "Dep. Cta. HARTGE JOSE NOLI", "", "", "2026-11-03", 2000000.00, "DEPOSITO EN CUENTA"),
            ("03", "Cobranza", "CORRIENTES S.A.", "31343291", "2026-10-26", 403333.33, "CHEQUE TERCERO"),
        ]
        download_pdf.return_value = self.pdf

        response = self._get(tipo="R", numero="000300018948")

        self.assertEqual(response.status_code, 200)
        payments = download_pdf.call_args.kwargs["payments"]
        self.assertEqual(len(payments), 2)
        self.assertEqual(payments[0]["amount"], "2000000.00")
        self.assertEqual(payments[0]["method"], "DEPOSITO EN CUENTA · Dep. Cta. HARTGE JOSE NOLI")
        valores = download_pdf.call_args.kwargs["valores"]
        self.assertEqual(len(valores), 2)
        self.assertEqual(valores[1]["method"], "CHEQUE TERCERO · Cobranza")

    @override_settings(EMPRESA_ID=2, ACCOUNTING_DB_ALIAS="default")
    @patch("api.views.Cliente.objects.get")
    @patch("api.models.CuentaCorrienteCliente.objects.using")
    @patch("api.models.Cobranzas.objects.using")
    @patch("api.views.connections")
    @patch("api.views.download_receipt_pdf")
    def test_recibo_normal_envia_aplicaciones_y_valores_de_caja(
        self, download_pdf, connections_mock, payments_using, account_using, customer_get
    ):
        customer_get.return_value = self.customer
        account_using.return_value.filter.return_value.exists.return_value = True
        applied = SimpleNamespace(
            monto=12684.00, tipo="R", codigo="F", detalle="Cobranza",
            banco="", numero="", vence=None,
        )
        payments_using.return_value.filter.return_value.order_by.return_value = [applied]
        cursor = connections_mock.__getitem__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("00", "Cobranza", "", "", "2026-10-27", 12684.00, "EFECTIVO"),
        ]
        download_pdf.return_value = self.pdf

        response = self._get(tipo="R", numero="000100172083")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            download_pdf.call_args.kwargs["payments"],
            [{
                "amount": "12684.00",
                "method": "R · F · Cobranza",
                "bank": None,
                "reference": None,
                "due_date": None,
            }],
        )
        self.assertEqual(
            download_pdf.call_args.kwargs["valores"],
            [{
                "amount": "12684.00",
                "method": "EFECTIVO · Cobranza",
                "bank": None,
                "reference": None,
                "due_date": "2026-10-27",
            }],
        )

    @override_settings(
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.services.erp_documents.urlopen")
    def test_erp_422_de_recibo_se_mapea_a_inconsistencia_de_aplicaciones(self, urlopen):
        urlopen.side_effect = HTTPError("https://erp.example", 422, "private validation", {}, None)

        with self.assertRaises(ReceiptApplicationMismatch):
            download_receipt_pdf(
                company_id=2,
                customer_code="00591",
                receipt_number="000100000001",
                payments=[{"amount": "1250.00", "method": "Transferencia"}],
            )

    @override_settings(
        ERP_DOCUMENT_RENDER_URL="https://erp.example/api/v1/documents/invoices/by-reference",
        ERP_DOCUMENT_API_TOKEN="integration-secret",
        ERP_DOCUMENT_TIMEOUT=8,
    )
    @patch("api.services.erp_documents.urlopen")
    def test_recibo_envia_valores_de_caja_al_erp(self, urlopen):
        urlopen.return_value.__enter__.return_value = self.erp_response

        download_receipt_pdf(
            company_id=2,
            customer_code="00591",
            receipt_number="000300018948",
            payments=[{"amount": "2403333.33", "method": "Cobranza"}],
            valores=[
                {"amount": "2000000.00", "method": "DEPOSITO EN CUENTA", "bank": None,
                 "reference": None, "due_date": "2026-11-03"},
                {"amount": "403333.33", "method": "CHEQUE TERCERO", "bank": "CORRIENTES S.A.",
                 "reference": "31343291", "due_date": "2026-10-26"},
            ],
        )

        request = urlopen.call_args.args[0]
        self.assertEqual(
            json.loads(request.data)["valores"],
            [
                {"amount": "2000000.00", "method": "DEPOSITO EN CUENTA", "bank": None,
                 "reference": None, "due_date": "2026-11-03"},
                {"amount": "403333.33", "method": "CHEQUE TERCERO", "bank": "CORRIENTES S.A.",
                 "reference": "31343291", "due_date": "2026-10-26"},
            ],
        )
