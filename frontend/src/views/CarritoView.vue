<template>
  <div class="ui-page space-y-6">
    <PageHeader
      title="Carrito de compras"
      description="Revisá cantidades, peso y total estimado antes de confirmar el pedido."
    >
      <template #actions>
        <ActionButton to="/productos" variant="secondary">
          Seguir comprando
        </ActionButton>
      </template>
    </PageHeader>

    <EmptyState
      v-if="cart.items.length === 0"
      title="Tu carrito está vacío"
      description="Buscá productos, agregá cantidades y armá el pedido para enviar a ventas."
    >
      <template #actions>
        <ActionButton to="/productos">
          Ver productos
        </ActionButton>
      </template>
    </EmptyState>

    <div v-else class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section class="space-y-4">
        <div class="ui-table-wrap hidden lg:block">
          <table class="ui-table">
            <thead>
              <tr>
                <th>Artículo</th>
                <th>Unidad</th>
                <th>Precio</th>
                <th>Cantidad</th>
                <th>Peso</th>
                <th>Subtotal</th>
                <th><span class="sr-only">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in cart.items" :key="item.articulo.clave">
                <td>
                  <div class="flex items-center gap-3">
                    <img class="h-14 w-14 rounded-lg border border-gray-200 object-contain" :src="item.articulo.imagen || '/placeholder.png'" :alt="item.articulo.nombre">
                    <div class="min-w-0">
                      <p class="font-semibold text-gray-950">{{ item.articulo.nombre }}</p>
                      <p class="text-sm text-gray-500">Clave: {{ item.articulo.clave }}</p>
                    </div>
                  </div>
                </td>
                <td class="text-sm font-semibold text-gray-700">{{ item.articulo.unidad || 'UN' }}</td>
                <td class="text-sm text-gray-900">$ {{ formatCurrency(item.precio_unitario) }}</td>
                <td>
                  <div class="flex items-center gap-2">
                    <input
                      type="number"
                      :min="getMinQuantity(item)"
                      :step="getStepQuantity(item)"
                      v-model.number="item.cantidad"
                      @change="handleQuantityChange(item)"
                      class="ui-field w-24 px-3 py-2 text-sm"
                    >
                    <span v-if="item.articulo.campoa1?.toLowerCase() === 'a' && item.articulo.mts2 > 0" class="text-xs text-gray-500">
                      {{ (item.cantidad / item.articulo.mts2).toFixed(0) }} cajas
                    </span>
                  </div>
                </td>
                <td class="text-sm text-gray-700">{{ formatWeight(item) }} kg</td>
                <td class="font-bold text-gray-950">$ {{ formatCurrency(item.subtotal) }}</td>
                <td class="text-right">
                  <button @click="cart.remove(item.articulo.clave)" class="text-sm font-semibold text-red-700 hover:text-red-900">
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="space-y-3 lg:hidden">
          <article v-for="item in cart.items" :key="item.articulo.clave" class="ui-panel p-4">
            <div class="flex gap-3">
              <img class="h-16 w-16 rounded-lg border border-gray-200 object-contain" :src="item.articulo.imagen || '/placeholder.png'" :alt="item.articulo.nombre">
              <div class="min-w-0 flex-1">
                <p class="font-bold text-gray-950">{{ item.articulo.nombre }}</p>
                <p class="text-sm text-gray-500">Clave: {{ item.articulo.clave }}</p>
                <p class="mt-1 text-sm font-semibold text-gray-700">$ {{ formatCurrency(item.precio_unitario) }} / {{ item.articulo.unidad || 'UN' }}</p>
              </div>
            </div>

            <div class="mt-4 grid grid-cols-2 gap-3">
              <label class="text-sm">
                <span class="font-semibold text-gray-700">Cantidad</span>
                <input
                  type="number"
                  :min="getMinQuantity(item)"
                  :step="getStepQuantity(item)"
                  v-model.number="item.cantidad"
                  @change="handleQuantityChange(item)"
                  class="ui-field mt-1 px-3 py-2"
                >
              </label>
              <div class="rounded-lg bg-gray-50 p-3 text-sm">
                <p class="font-semibold text-gray-700">Peso</p>
                <p class="mt-1 text-gray-950">{{ formatWeight(item) }} kg</p>
              </div>
            </div>

            <div class="mt-4 flex items-center justify-between border-t border-gray-200 pt-3">
              <p class="text-lg font-black text-gray-950">$ {{ formatCurrency(item.subtotal) }}</p>
              <button @click="cart.remove(item.articulo.clave)" class="text-sm font-semibold text-red-700">
                Eliminar
              </button>
            </div>
          </article>
        </div>
      </section>

      <CartSummary
        :total="formatCurrency(cart.totalPrice)"
        :totalWeight="formatWeightDisplay(totalWeight)"
        :itemsCount="cart.totalItems"
        :loading="loading"
        :loadingLabel="processingStep || 'Procesando pedido...'"
        :disabled="cart.items.length === 0"
        @checkout="checkout"
      />
    </div>

    <div v-if="notification.message" :class="notificationClasses" class="fixed right-4 top-20 z-50 flex w-[calc(100%-2rem)] max-w-sm items-center justify-between gap-2 rounded-lg px-5 py-3 text-sm text-white shadow-lg">
      <span>{{ notification.message }}</span>
      <button @click="notification = { message: '', type: '' }" class="flex-shrink-0 text-white hover:text-gray-200" aria-label="Cerrar notificación">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cart } from '@/services/cart'
import ActionButton from '@/components/ui/ActionButton.vue'
import CartSummary from '@/components/ui/CartSummary.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'

const router = useRouter()
const loading = ref(false)
const processingStep = ref('')
const notification = ref({ message: '', type: '' })

const formatCurrency = (value) => {
  const number = parseFloat(value)
  if (isNaN(number)) return value
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number)
}

const formatWeightDisplay = (value) => {
  const number = parseFloat(value)
  if (isNaN(number)) return '0.000'
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(number)
}

const formatWeight = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase()
  const pesoUnitario = parseFloat(item.articulo.peso) || 0

  if (campoa1Lower === 'a' && item.articulo.mts2 > 0) {
    const cajas = item.cantidad / item.articulo.mts2
    return (cajas * pesoUnitario).toFixed(3)
  }

  return (item.cantidad * pesoUnitario).toFixed(3)
}

const totalWeight = computed(() => {
  return cart.items.reduce((total, item) => {
    const peso = parseFloat(formatWeight(item)) || 0
    return total + peso
  }, 0)
})

const getMinQuantity = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase()
  if (campoa1Lower === 'a' && item.articulo.mts2 > 0) {
    return item.articulo.mts2
  }
  return 1
}

const getStepQuantity = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase()
  if (campoa1Lower === 'a' && item.articulo.mts2 > 0) {
    return item.articulo.mts2
  }
  return 1
}

const handleQuantityChange = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase()

  if (campoa1Lower === 'a' && item.articulo.mts2 > 0 && item.cantidad > 0) {
    const mts2 = parseFloat(item.articulo.mts2)
    const cajas = Math.ceil(item.cantidad / mts2)
    const cantidadAjustada = cajas * mts2

    if (Math.abs(item.cantidad - cantidadAjustada) > 0.01) {
      item.cantidad = cantidadAjustada
      showNotification(`Cantidad ajustada a ${cantidadAjustada.toFixed(2)} m² (${cajas} caja${cajas > 1 ? 's' : ''})`, 'info')
    }
  }

  cart.updateQuantity(item.articulo.clave, item.cantidad)
}

const notificationClasses = computed(() => ({
  'bg-green-700': notification.value.type === 'success',
  'bg-red-700': notification.value.type === 'error',
  'bg-blue-700': notification.value.type === 'info',
}))

const showNotification = (message, type) => {
  notification.value = { message, type }
  const duration = type === 'error' ? 5000 : 3000
  setTimeout(() => {
    notification.value = { message: '', type: '' }
  }, duration)
}

const checkout = async () => {
  if (cart.items.length === 0) {
    showNotification('El carrito está vacío', 'error')
    return
  }

  loading.value = true
  processingStep.value = 'Procesando pedido...'

  try {
    const result = await cart.checkout((step) => {
      processingStep.value = step
    })

    if (result.success) {
      processingStep.value = 'Pedido confirmado'
      showNotification(result.message || 'Pedido realizado con éxito. Recibirás un correo de confirmación.', 'success')
      setTimeout(() => {
        const pedidoId = result.pedido?.id || 'N/A'
        router.push(`/pedido-confirmado/${pedidoId}`)
      }, 1500)
    } else {
      processingStep.value = 'Error en el proceso'
      showNotification(result.message || 'Error al procesar el pedido. Intente de nuevo.', 'error')
    }
  } catch (error) {
    let errorMessage = 'Error al procesar el pedido. Intente de nuevo.'

    if (error.response) {
      if (error.response.status === 401) {
        errorMessage = 'Su sesión ha expirado. Inicie sesión nuevamente.'
      } else if (error.response.status === 400) {
        errorMessage = error.response.data?.error || 'Datos del pedido inválidos.'
      } else if (error.response.status >= 500) {
        errorMessage = 'Error interno del servidor. Intente más tarde.'
      }
    } else if (error.message && error.message.includes('Timeout')) {
      errorMessage = 'El proceso tardó más de lo esperado. Verifique su pedido en su cuenta.'
    } else if (error.code === 'NETWORK_ERROR') {
      errorMessage = 'Error de conexión. Verifique su conexión a internet.'
    }

    processingStep.value = 'Error en el proceso'
    showNotification(errorMessage, 'error')
  } finally {
    loading.value = false
    processingStep.value = ''
  }
}
</script>
