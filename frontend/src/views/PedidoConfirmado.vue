<template>
  <div class="ui-page min-h-screen bg-gray-50 px-4 py-8 sm:px-6">
    <div class="mx-auto max-w-3xl space-y-6">
      <section class="rounded-2xl border border-green-200 bg-white p-6 text-center shadow-sm sm:p-8">
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-green-700">
          <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p class="text-sm font-bold uppercase tracking-wide text-green-700">Solicitud recibida por FASA</p>
        <h1 class="mt-2 text-3xl font-black text-gray-950">Pedido enviado</h1>
        <p class="mt-3 text-base text-gray-600">
          Recibimos tu pedido y Ventas lo revisará para confirmar stock, precio final y condiciones comerciales.
        </p>
      </section>

      <section v-if="loading" class="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <p class="font-semibold text-gray-600">Cargando datos del pedido...</p>
      </section>

      <section v-else-if="errorMessage" class="rounded-2xl border border-yellow-200 bg-yellow-50 p-5 text-yellow-900">
        <p class="font-bold">El pedido fue enviado.</p>
        <p class="mt-1 text-sm">{{ errorMessage }}</p>
      </section>

      <template v-else-if="pedido">
        <section class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-6">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-sm font-semibold text-gray-500">Número de pedido</p>
              <p class="mt-1 text-2xl font-black text-gray-950">#{{ pedido.id }}</p>
            </div>
            <div class="rounded-xl bg-red-50 px-4 py-3 text-left sm:text-right">
              <p class="text-xs font-bold uppercase text-red-700">Total estimado</p>
              <p class="mt-1 text-2xl font-black text-red-800">$ {{ formatCurrency(pedido.total) }}</p>
            </div>
          </div>

          <dl class="mt-6 grid gap-4 sm:grid-cols-2">
            <div class="rounded-xl bg-gray-50 p-4">
              <dt class="text-xs font-bold uppercase text-gray-500">Modalidad</dt>
              <dd class="mt-1 font-bold text-gray-900">{{ modalidadLabel }}</dd>
            </div>
            <div class="rounded-xl bg-gray-50 p-4">
              <dt class="text-xs font-bold uppercase text-gray-500">Condición de pago</dt>
              <dd class="mt-1 font-bold text-gray-900">{{ condicionPagoLabel }}</dd>
            </div>
            <div class="rounded-xl bg-gray-50 p-4">
              <dt class="text-xs font-bold uppercase text-gray-500">Impuestos</dt>
              <dd class="mt-1 font-bold text-gray-900">{{ pedido.con_impuestos ? 'Con impuestos' : 'Sin impuestos' }}</dd>
            </div>
            <div class="rounded-xl bg-gray-50 p-4">
              <dt class="text-xs font-bold uppercase text-gray-500">Estado de email</dt>
              <dd class="mt-1 font-bold text-gray-900">{{ emailLabel }}</dd>
            </div>
          </dl>

          <div v-if="pedido.cliente_snapshot?.observaciones" class="mt-4 rounded-xl border border-gray-200 p-4">
            <p class="text-xs font-bold uppercase text-gray-500">Observaciones</p>
            <p class="mt-2 whitespace-pre-line text-sm text-gray-800">{{ pedido.cliente_snapshot.observaciones }}</p>
          </div>
        </section>

        <section class="rounded-2xl border border-blue-200 bg-blue-50 p-5 text-blue-950">
          <h2 class="font-black">Importante</h2>
          <p class="mt-2 text-sm leading-6">
            No se realizó ningún pago online. El importe mostrado es estimado. Ventas confirmará disponibilidad,
            precio final, bonificaciones, forma de entrega y demás condiciones antes de cerrar la operación.
          </p>
        </section>

        <section class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-6">
          <h2 class="text-lg font-black text-gray-950">Resumen de productos</h2>
          <div class="mt-4 divide-y divide-gray-100">
            <div v-for="item in pedido.items || []" :key="item.id" class="flex gap-4 py-4">
              <div class="min-w-0 flex-1">
                <p class="font-bold text-gray-950">{{ item.articulo_detalle?.nombre || item.articulo }}</p>
                <p class="mt-1 text-sm text-gray-500">Cantidad: {{ item.cantidad }}</p>
              </div>
              <div class="text-right">
                <p class="text-sm text-gray-500">Subtotal estimado</p>
                <p class="font-black text-gray-950">$ {{ formatCurrency(item.subtotal) }}</p>
              </div>
            </div>
          </div>
        </section>
      </template>

      <div class="grid gap-3 sm:grid-cols-2">
        <router-link to="/pedidos" class="rounded-xl bg-red-700 px-5 py-3 text-center font-bold text-white transition hover:bg-red-800">
          Ver mis pedidos
        </router-link>
        <router-link to="/productos" class="rounded-xl border border-gray-300 bg-white px-5 py-3 text-center font-bold text-gray-800 transition hover:bg-gray-50">
          Armar otro pedido
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const pedido = ref(null)
const loading = ref(true)
const errorMessage = ref('')

const formatCurrency = (value) => new Intl.NumberFormat('es-AR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(Number(value || 0))

const modalidadLabel = computed(() => {
  if (!pedido.value) return '-'
  return pedido.value.modalidad === 'reparto' ? 'Reparto' : 'Retira en FASA'
})

const condicionPagoLabel = computed(() => {
  if (!pedido.value) return '-'
  return pedido.value.cliente_snapshot?.condicion_pago_nombre || pedido.value.condicion_pago || 'A confirmar'
})

const emailLabel = computed(() => {
  if (!pedido.value) return '-'
  if (pedido.value.email_cliente_estado === 'ENVIADO') return 'Copia enviada por email'
  if (pedido.value.email_cliente_estado === 'FALLIDO') return 'Pedido guardado; email pendiente de reintento'
  return 'En proceso de envío'
})

onMounted(async () => {
  const pedidoId = route.params.id || route.query.pedido
  if (!pedidoId) {
    errorMessage.value = 'No pudimos identificar el número de pedido en esta pantalla.'
    loading.value = false
    return
  }

  try {
    const response = await api.get(`/api/pedidos/${pedidoId}/`)
    pedido.value = response.data
  } catch (error) {
    errorMessage.value = 'No pudimos cargar el detalle en este momento. Podés verlo desde “Mis pedidos”.'
  } finally {
    loading.value = false
  }
})
</script>
