from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from api.models import Pedido
from api.services.notificaciones_pedido import enviar_notificaciones_pedido


@override_settings(DEFAULT_FROM_EMAIL='ventas@fasa.test', EMAIL_RECIPIENT='pedidos@fasa.test')
class PedidoNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mail-test', email='cliente@fasa.test')
        self.pedido = Pedido.objects.create(
            user=self.user,
            estado='CONFIRMADO',
            total='1250.50',
            modalidad='reparto',
            con_impuestos=True,
            cliente_snapshot={
                'numero_cliente': '00125',
                'nombre': 'CLIENTE PRUEBA',
                'email': 'cliente@fasa.test',
                'condicion_pago_nombre': 'Cuenta corriente 30 días',
                'localidad': 'Puerto Rico',
                'direccion': 'Av. San Martín 123',
                'observaciones': 'Entregar por portón lateral',
            },
        )

    @patch('api.services.notificaciones_pedido.send_mail', return_value=1)
    def test_envio_exitoso_registra_ambos_destinos(self, mocked):
        result = enviar_notificaciones_pedido(self.pedido.id)
        self.pedido.refresh_from_db()
        self.assertEqual(result['cliente']['estado'], 'ENVIADO')
        self.assertEqual(result['ventas']['estado'], 'ENVIADO')
        self.assertEqual(self.pedido.email_cliente_intentos, 1)
        self.assertEqual(self.pedido.email_ventas_intentos, 1)
        self.assertEqual(mocked.call_count, 2)

        llamada_cliente = mocked.call_args_list[0]
        self.assertEqual(llamada_cliente.args[0], f'[FASA] Pedido recibido #{self.pedido.id}')
        self.assertIn('No se realizó ningún pago online', llamada_cliente.args[1])
        self.assertIn('Ventas confirmará stock, precio final y condiciones', llamada_cliente.args[1])

        llamada_ventas = mocked.call_args_list[1]
        asunto_ventas = llamada_ventas.args[0]
        self.assertIn('[FASA] Nuevo pedido #', asunto_ventas)
        self.assertIn('Cliente 00125', asunto_ventas)
        self.assertIn('CLIENTE PRUEBA', asunto_ventas)
        self.assertIn('Entregar por portón lateral', llamada_ventas.args[1])
        self.assertIn('Reparto', llamada_ventas.args[1])

    @patch('api.services.notificaciones_pedido.send_mail', side_effect=RuntimeError('SMTP fuera de servicio'))
    def test_fallo_queda_persistido(self, _mocked):
        result = enviar_notificaciones_pedido(self.pedido.id, destinos=('cliente',))
        self.pedido.refresh_from_db()
        self.assertEqual(result['cliente']['estado'], 'FALLIDO')
        self.assertEqual(self.pedido.email_cliente_estado, 'FALLIDO')
        self.assertEqual(self.pedido.email_cliente_intentos, 1)
        self.assertIn('SMTP fuera de servicio', self.pedido.email_cliente_ultimo_error)

    @patch('api.services.notificaciones_pedido.send_mail', return_value=1)
    def test_reintento_incrementa_intentos_y_recupera(self, _mocked):
        self.pedido.email_cliente_estado = 'FALLIDO'
        self.pedido.email_cliente_intentos = 1
        self.pedido.email_cliente_ultimo_error = 'error anterior'
        self.pedido.save()
        enviar_notificaciones_pedido(self.pedido.id, destinos=('cliente',))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.email_cliente_estado, 'ENVIADO')
        self.assertEqual(self.pedido.email_cliente_intentos, 2)
        self.assertEqual(self.pedido.email_cliente_ultimo_error, '')
