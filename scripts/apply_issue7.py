from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1) Backend serializer: aceptar observaciones y congelarlas en el snapshot.
path = ROOT / 'backend/api/serializers.py'
text = path.read_text(encoding='utf-8')
text = text.replace(
    "class PedidoSerializer(serializers.ModelSerializer):\n    items = PedidoItemSerializer(many=True)\n",
    "class PedidoSerializer(serializers.ModelSerializer):\n    items = PedidoItemSerializer(many=True)\n    observaciones = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=1000)\n",
    1,
)
text = text.replace(
    "'email_ventas_ultimo_error', 'items']",
    "'email_ventas_ultimo_error', 'observaciones', 'items']",
    1,
)
text = text.replace(
    "        items_data = validated_data.pop('items')\n        user = validated_data.get('user')\n",
    "        items_data = validated_data.pop('items')\n        observaciones = validated_data.pop('observaciones', '').strip()\n        user = validated_data.get('user')\n",
    1,
)
text = text.replace(
    "            'condicion_pago_nombre': condicion_pago.nombre if condicion_pago else '',\n        }",
    "            'condicion_pago_nombre': condicion_pago.nombre if condicion_pago else '',\n            'observaciones': observaciones,\n        }",
    1,
)
path.write_text(text, encoding='utf-8')

# 2) Cart service: permitir overrides de revisión final sin romper callers previos.
path = ROOT / 'frontend/src/services/cart.js'
text = path.read_text(encoding='utf-8')
text = text.replace(
    "    async checkout(onProgress = null) {",
    "    async checkout(onProgress = null, overrides = {}) {",
    1,
)
text = text.replace(
    "            const modalidad = localStorage.getItem('articulos_modalidad') || 'retira';\n            const savedImpuestos = localStorage.getItem('articulos_con_impuestos');\n            const con_impuestos = savedImpuestos === null ? true : savedImpuestos === 'true';\n            const condicion_pago = localStorage.getItem('condicion_pago');",
    "            const modalidad = overrides.modalidad || localStorage.getItem('articulos_modalidad') || 'retira';\n            const savedImpuestos = localStorage.getItem('articulos_con_impuestos');\n            const con_impuestos = overrides.con_impuestos ?? (savedImpuestos === null ? true : savedImpuestos === 'true');\n            const condicion_pago = overrides.condicion_pago || localStorage.getItem('condicion_pago');",
    1,
)
text = text.replace(
    "                ...(condicion_pago ? { condicion_pago } : {}),\n                items:",
    "                ...(condicion_pago ? { condicion_pago } : {}),\n                ...(overrides.observaciones ? { observaciones: overrides.observaciones } : {}),\n                items:",
    1,
)
path.write_text(text, encoding='utf-8')

# 3) Carrito: el botón ya no envía, lleva a la revisión.
path = ROOT / 'frontend/src/views/CarritoView.vue'
text = path.read_text(encoding='utf-8')
start = text.index('const checkout = async () => {')
end = text.index('\n</script>', start)
replacement = "const checkout = () => {\n  if (cart.items.length === 0) {\n    showNotification('El carrito está vacío', 'error')\n    return\n  }\n  router.push('/revisar-pedido')\n}\n"
text = text[:start] + replacement + text[end:]
path.write_text(text, encoding='utf-8')

# 4) Router: nueva pantalla de revisión.
path = ROOT / 'frontend/src/router/index.js'
text = path.read_text(encoding='utf-8')
needle = "  { \n    path: '/pedidos', \n    component: () => import('@/views/PedidosView.vue'), \n    meta: { requiresAuth: true } \n  },"
route = "  {\n    path: '/revisar-pedido',\n    name: 'revisar-pedido',\n    component: () => import('@/views/RevisarPedidoView.vue'),\n    meta: { requiresAuth: true }\n  },\n" + needle
text = text.replace(needle, route, 1)
path.write_text(text, encoding='utf-8')

# 5) Vista de revisión final.
review = '''<template>
  <div class="ui-page space-y-6 pb-10">
    <PageHeader
      title="Revisar y enviar pedido"
      description="Confirmá productos y condiciones antes de enviar la solicitud a Ventas FASA."
    >
      <template #actions>
        <ActionButton to="/carrito" variant="secondary">Volver a editar</ActionButton>
      </template>
    </PageHeader>

    <EmptyState
      v-if="cart.items.length === 0"
      title="No hay productos para revisar"
      description="Volvé al catálogo y agregá productos al carrito."
    >
      <template #actions><ActionButton to="/productos">Ver productos</ActionButton></template>
    </EmptyState>

    <div v-else class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div class="space-y-6">
        <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex items-center justify-between gap-4 border-b border-gray-100 pb-4">
            <div>
              <h2 class="text-lg font-black text-gray-950">Productos</h2>
              <p class="text-sm text-gray-600">{{ cart.totalItems }} artículos · {{ formatWeight(totalWeight) }} kg estimados</p>
            </div>
            <RouterLink to="/carrito" class="text-sm font-bold text-red-700 hover:text-red-900">Editar carrito</RouterLink>
          </div>
          <div class="divide-y divide-gray-100">
            <article v-for="item in cart.items" :key="item.articulo.clave" class="grid gap-3 py-4 sm:grid-cols-[1fr_auto] sm:items-center">
              <div>
                <p class="font-bold text-gray-950">{{ item.articulo.nombre }}</p>
                <p class="mt-1 text-sm text-gray-600">{{ item.articulo.clave }} · {{ item.cantidad }} {{ item.articulo.unidad || 'UN' }}</p>
              </div>
              <div class="sm:text-right">
                <p class="text-sm text-gray-500">$ {{ money(item.precio_unitario) }} c/u</p>
                <p class="text-lg font-black text-gray-950">$ {{ money(item.subtotal) }}</p>
              </div>
            </article>
          </div>
        </section>

        <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 class="text-lg font-black text-gray-950">Condiciones del pedido</h2>
          <div class="mt-5 grid gap-5 md:grid-cols-2">
            <label class="block">
              <span class="mb-2 block text-sm font-bold text-gray-700">Modalidad</span>
              <select v-model="modalidad" class="h-11 w-full rounded-lg border border-gray-300 bg-white px-3 font-semibold focus:border-red-600 focus:outline-none focus:ring-4 focus:ring-red-100">
                <option value="retira">Retira en FASA</option>
                <option value="reparto">Reparto</option>
              </select>
            </label>
            <div>
              <span class="mb-2 block text-sm font-bold text-gray-700">Condición comercial</span>
              <div class="flex h-11 items-center rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-semibold text-gray-800">
                {{ condicionPago ? `Condición ${condicionPago}` : 'Condición habitual de la cuenta' }}
              </div>
            </div>
            <div>
              <span class="mb-2 block text-sm font-bold text-gray-700">Impuestos</span>
              <div class="flex h-11 items-center rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-semibold text-gray-800">
                {{ conImpuestos ? 'Precios con impuestos' : 'Precios sin impuestos' }}
              </div>
            </div>
            <div v-if="modalidad === 'reparto'" class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              Ventas confirmará disponibilidad de reparto y datos finales de entrega con la información de tu cuenta.
            </div>
          </div>
          <label class="mt-5 block">
            <span class="mb-2 block text-sm font-bold text-gray-700">Observaciones</span>
            <textarea
              v-model.trim="observaciones"
              maxlength="1000"
              rows="4"
              placeholder="Referencias, horarios, aclaraciones de entrega u otra información para Ventas."
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-3 text-sm focus:border-red-600 focus:outline-none focus:ring-4 focus:ring-red-100"
            />
            <span class="mt-1 block text-right text-xs text-gray-500">{{ observaciones.length }}/1000</span>
          </label>
        </section>
      </div>

      <aside class="h-fit rounded-xl border border-gray-200 bg-white p-5 shadow-sm xl:sticky xl:top-24">
        <p class="text-sm font-bold uppercase tracking-wide text-red-700">Resumen</p>
        <div class="mt-4 flex items-end justify-between gap-4 border-b border-gray-100 pb-4">
          <span class="font-semibold text-gray-700">Total estimado</span>
          <strong class="text-2xl font-black text-gray-950">$ {{ money(cart.totalPrice) }}</strong>
        </div>
        <div class="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm leading-6 text-blue-950">
          <strong>No se realiza ningún pago online.</strong> Este envío genera una solicitud de pedido. Ventas FASA confirmará disponibilidad, precio final y condiciones.
        </div>
        <button
          type="button"
          :disabled="sending || cart.items.length === 0"
          class="mt-5 inline-flex min-h-12 w-full items-center justify-center rounded-lg bg-red-700 px-5 py-3 text-sm font-black text-white shadow-sm transition hover:bg-red-800 disabled:cursor-not-allowed disabled:opacity-60"
          @click="sendOrder"
        >
          {{ sending ? 'ENVIANDO PEDIDO...' : 'ENVIAR PEDIDO A FASA' }}
        </button>
        <p v-if="errorMessage" class="mt-3 rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-800">{{ errorMessage }}</p>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { cart } from '@/services/cart'
import ActionButton from '@/components/ui/ActionButton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'

const router = useRouter()
const modalidad = ref(localStorage.getItem('articulos_modalidad') || 'retira')
const savedImpuestos = localStorage.getItem('articulos_con_impuestos')
const conImpuestos = ref(savedImpuestos === null ? true : savedImpuestos === 'true')
const condicionPago = ref(localStorage.getItem('condicion_pago') || '')
const observaciones = ref('')
const sending = ref(false)
const errorMessage = ref('')

watch(modalidad, value => localStorage.setItem('articulos_modalidad', value))

const itemWeight = item => {
  const qty = Number(item.cantidad) || 0
  const weight = Number(item.articulo.peso) || 0
  const mts2 = Number(item.articulo.mts2) || 0
  if ((item.articulo.campoa1 || '').toLowerCase() === 'a' && mts2 > 0) return (qty / mts2) * weight
  return qty * weight
}
const totalWeight = computed(() => cart.items.reduce((sum, item) => sum + itemWeight(item), 0))
const formatWeight = value => new Intl.NumberFormat('es-AR', { minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(Number(value) || 0)
const money = value => new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value) || 0)

const sendOrder = async () => {
  if (sending.value || cart.items.length === 0) return
  sending.value = true
  errorMessage.value = ''
  try {
    const result = await cart.checkout(null, {
      modalidad: modalidad.value,
      con_impuestos: conImpuestos.value,
      condicion_pago: condicionPago.value || undefined,
      observaciones: observaciones.value,
    })
    if (!result.success) {
      errorMessage.value = result.message || 'No se pudo enviar el pedido.'
      return
    }
    router.push(`/pedido-confirmado/${result.pedido?.id || ''}`)
  } finally {
    sending.value = false
  }
}
</script>
'''
(ROOT / 'frontend/src/views/RevisarPedidoView.vue').write_text(review, encoding='utf-8')

# 6) Test backend de observaciones/snapshot.
test = '''from datetime import date\nfrom decimal import Decimal\n\nfrom django.contrib.auth.models import User\nfrom django.test import TestCase\n\nfrom api.models import Articulos, Cliente, FormaPago, Localidades\nfrom api.serializers import PedidoSerializer\n\n\nclass PedidoReviewDataTests(TestCase):\n    def test_observaciones_quedan_en_snapshot(self):\n        forma = FormaPago.objects.create(id='00', nombre='Contado', descuento=0, punitorio=0)\n        localidad = Localidades.objects.create(codigo='0099', nombre='Puerto Rico')\n        user = User.objects.create_user(username='review-user', password='test')\n        Cliente.objects.create(\n            user=user, numero_cliente='990', lista_precio='1', nombre='Cliente Review',\n            codigo_localidad=localidad, condicion_pago=forma, tipo_responsable_iva='C'\n        )\n        articulo = Articulos.objects.create(\n            clave='099.001', unidad='UN', nombre='Articulo Review', peso=Decimal('1'),\n            pblret1=Decimal('10'), pblrep1=Decimal('10'), pblret4=Decimal('10'), pblrep4=Decimal('10'),\n            ultact=date.today(), visible='S', descripcion='Review', iva=0\n        )\n        serializer = PedidoSerializer(data={\n            'modalidad': 'reparto', 'con_impuestos': True, 'condicion_pago': '00',\n            'observaciones': 'Entregar por la tarde',\n            'items': [{'articulo': articulo.clave, 'cantidad': '1', 'precio_unitario': '10.00'}],\n        })\n        self.assertTrue(serializer.is_valid(), serializer.errors)\n        pedido = serializer.save(user=user)\n        self.assertEqual(pedido.cliente_snapshot['observaciones'], 'Entregar por la tarde')\n        self.assertEqual(pedido.modalidad, 'reparto')\n'''
(ROOT / 'backend/api/tests/test_pedido_review.py').write_text(test, encoding='utf-8')
