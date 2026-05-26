<template>
  <div 
    v-if="modelValue" 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    @click.self="$emit('update:modelValue', false)"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header del Modal -->
      <div class="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
        <div>
          <h2 class="text-xl font-semibold text-gray-900">
            {{ detalle?.encabezado?.tipo_comprobante || 'Detalle del Comprobante' }}
            {{ detalle?.encabezado?.numero }}
          </h2>
          <p v-if="detalle?.encabezado?.cliente" class="text-sm text-gray-600">
            {{ detalle.encabezado.cliente.nombre }}
          </p>
        </div>
        <button
          @click="$emit('update:modelValue', false)"
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <i class="fas fa-times text-xl"></i>
        </button>
      </div>

      <!-- Debug panel (visible con ?debug=1 o si se activa en localStorage) -->
      <div v-if="showDebug" class="px-6 py-4 border-b bg-gray-50">
        <div class="flex items-center justify-between mb-2">
          <strong class="text-sm text-gray-700">Debug info</strong>
          <div class="flex gap-2">
            <button @click="persistDebug" class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Persistir</button>
            <button @click="clearPersistDebug" class="text-xs px-2 py-1 bg-red-100 text-red-700 rounded">Quitar persistencia</button>
          </div>
        </div>
        <pre class="text-xs text-gray-700 max-h-40 overflow-auto bg-white p-2 border rounded">{{ JSON.stringify(debugInfo, null, 2) }}</pre>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="p-8 text-center">
        <i class="fas fa-spinner fa-spin text-2xl text-blue-600 mb-4"></i>
        <p class="text-gray-600">Cargando detalle del comprobante...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="p-6">
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
          <div class="flex items-center">
            <i class="fas fa-exclamation-triangle text-red-500 mr-2"></i>
            <div>
              <h3 class="text-red-800 font-medium">Error al cargar el detalle</h3>
              <p class="text-red-600 text-sm mt-1">{{ error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Contenido - No implementado (Código R) -->
      <div v-else-if="!detalle?.data && detalle?.message" class="p-6">
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div class="flex items-center">
            <i class="fas fa-info-circle text-yellow-500 mr-3"></i>
            <div>
              <h3 class="text-yellow-800 font-medium">Funcionalidad no disponible</h3>
              <p class="text-yellow-600 text-sm mt-1">{{ detalle.message }}</p>
              <div v-if="detalle.comprobante" class="mt-3 text-sm text-gray-700">
                <p><strong>Número:</strong> {{ detalle.comprobante.numero }}</p>
                <p><strong>Tipo:</strong> {{ detalle.comprobante.tipo }}</p>
                <p><strong>Fecha:</strong> {{ formatDate(detalle.comprobante.fecha) }}</p>
                <p><strong>Total:</strong> ${{ formatCurrency(detalle.comprobante.total) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Contenido Principal -->
      <div v-else-if="detalle?.data" class="p-6">
        <!-- Información del Encabezado -->
        <div class="bg-gray-50 rounded-lg p-4 mb-6">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label class="text-sm font-medium text-gray-600">Fecha</label>
              <p class="text-gray-900">{{ formatDate(detalle.data.encabezado.fecha) }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Vencimiento</label>
              <p class="text-gray-900">{{ formatDate(detalle.data.encabezado.fecha_vencimiento) }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Estado</label>
              <span :class="{
                'bg-green-100 text-green-800': detalle.data.encabezado.estado === 'Vigente',
                'bg-red-100 text-red-800': detalle.data.encabezado.estado === 'Vencido'
              }" class="inline-flex px-2 py-1 text-xs font-semibold rounded-full">
                {{ detalle.data.encabezado.estado }}
              </span>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Localidad</label>
              <p class="text-gray-900">{{ detalle.data.encabezado.localidad || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Forma de Pago</label>
              <p class="text-gray-900">{{ detalle.data.encabezado.forma_pago || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Vendedor</label>
              <p class="text-gray-900">{{ detalle.data.encabezado.vendedor || '-' }}</p>
            </div>
          </div>
        </div>

          <!-- Tabla de Items -->
          <div class="mb-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">
              {{ isRecibo ? 'Detalle de Pagos / Recibos' : 'Detalle de Items' }}
            </h3>

            <div class="overflow-x-auto">
              <!-- Tabla para recibos/pagos -->
              <table v-if="isRecibo" class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detalle</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Banco</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Número</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Vence</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Imp./Imprenta</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monto</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(item, idx) in detalle.data.items" :key="idx" class="hover:bg-gray-50">
                    <td class="px-3 py-4 text-sm text-gray-900">{{ item.tipo || '-' }}</td>
                    <td class="px-3 py-4 text-sm text-gray-700">{{ item.detalle || item.comp || '-' }}</td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">{{ item.banco || '-' }}</td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">{{ item.numero || '-' }}</td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">{{ formatDate(item.vence) }}</td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">${{ formatCurrency(item.impentra) }}</td>
                    <td class="px-3 py-4 text-right text-sm font-medium text-gray-900">${{ formatCurrency(item.monto) }}</td>
                  </tr>
                </tbody>
              </table>

              <!-- Tabla para facturas/débito/crédito (por defecto) -->
              <table v-else class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Artículo</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cantidad</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">% Bonif.</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">IVA</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="item in detalle.data.items" :key="item.item" class="hover:bg-gray-50">
                    <td class="px-3 py-4">
                      <div>
                        <p class="text-sm font-medium text-gray-900">{{ item.articulo.clave }}</p>
                        <p class="text-sm text-gray-500">{{ item.articulo.descripcion }}</p>
                        <p class="text-xs text-gray-400">{{ item.articulo.unidad }}</p>
                      </div>
                    </td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">
                      {{ formatNumber(item.cantidad) }}
                    </td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">
                      ${{ formatCurrency(item.precio_unitario) }}
                    </td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">
                      {{ formatNumber(item.bonificacion) }}%
                    </td>
                    <td class="px-3 py-4 text-right text-sm text-gray-900">
                      {{ formatNumber(item.alicuota_iva) }}%
                    </td>
                    <td class="px-3 py-4 text-right text-sm font-medium text-gray-900">
                      ${{ formatCurrency(item.total_renglon) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        <!-- Resumen de Totales (diferente para recibos vs facturas) -->
        <div class="bg-gray-50 rounded-lg p-4">
          <template v-if="isRecibo">
            <div class="flex justify-between items-center text-sm mb-2">
              <span class="text-gray-600">Total Pagos:</span>
              <span class="text-gray-900">${{ formatCurrency(detalle.data.resumen.total_monto) }}</span>
            </div>
            <div class="border-t pt-2 mt-2">
              <div class="flex justify-between items-center text-base font-semibold">
                <span class="text-gray-900">Cantidad de movimientos:</span>
                <span class="text-gray-900">{{ detalle.data.resumen.cantidad_items }}</span>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="flex justify-between items-center text-sm mb-2">
              <span class="text-gray-600">Subtotal:</span>
              <span class="text-gray-900">${{ formatCurrency(detalle.data.encabezado.totales.subtotal) }}</span>
            </div>
            <div class="flex justify-between items-center text-sm mb-2">
              <span class="text-gray-600">IVA:</span>
              <span class="text-gray-900">${{ formatCurrency(detalle.data.encabezado.totales.iva) }}</span>
            </div>
            <div v-if="detalle.data.encabezado.totales.percepcion_dgr > 0" class="flex justify-between items-center text-sm mb-2">
              <span class="text-gray-600">Percepción DGR:</span>
              <span class="text-gray-900">${{ formatCurrency(detalle.data.encabezado.totales.percepcion_dgr) }}</span>
            </div>
            <div class="border-t pt-2 mt-2">
              <div class="flex justify-between items-center text-base font-semibold">
                <span class="text-gray-900">Total:</span>
                <span class="text-gray-900">${{ formatCurrency(detalle.data.encabezado.totales.total) }}</span>
              </div>
              <div class="flex justify-between items-center text-sm mt-1">
                <span class="text-gray-600">Saldo Pendiente:</span>
                <span :class="{
                  'text-red-600': detalle.data.encabezado.totales.saldo > 0,
                  'text-green-600': detalle.data.encabezado.totales.saldo <= 0
                }" class="font-medium">
                  ${{ formatCurrency(detalle.data.encabezado.totales.saldo) }}
                </span>
              </div>
            </div>
          </template>
        </div>

        <!-- Resumen de Items -->
        <div v-if="detalle.data.resumen" class="mt-4 text-sm text-gray-600 text-center">
          {{ detalle.data.resumen.cantidad_items }} items • 
          {{ formatNumber(detalle.data.resumen.peso_total) }} unidades totales
        </div>
      </div>

      <!-- Footer -->
      <div class="sticky bottom-0 bg-white border-t px-6 py-4 flex justify-end">
        <button
          @click="$emit('update:modelValue', false)"
          class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { getDetalleComprobante } from '@/services/dashboard'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  numeroComprobante: {
    type: String,
    required: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue'])

// State
const loading = ref(false)
const error = ref(null)
const detalle = ref(null)
const debugInfo = ref(null)

// Mostrar panel debug si estamos en dev o si se pasa ?debug=1 o se activa en localStorage
const showDebug = computed(() => {
  try {
    const urlDebug = new URL(window.location.href).searchParams.get('debug') === '1'
    return import.meta.env.DEV || urlDebug || localStorage.getItem('debug_detalle') === '1'
  } catch (e) {
    return import.meta.env.DEV || localStorage.getItem('debug_detalle') === '1'
  }
})

// Determina si el comprobante es un recibo/pago (codigo 'R')
const isRecibo = computed(() => {
  try {
    return !!(detalle.value && (detalle.value.data?.encabezado?.codigo === 'R' || (detalle.value.data?.encabezado?.tipo_comprobante || '').toString().toLowerCase().includes('recibo')))
  } catch (e) {
    return false
  }
})

const persistDebug = () => localStorage.setItem('debug_detalle', '1')
const clearPersistDebug = () => localStorage.removeItem('debug_detalle')

// Methods
const formatCurrency = (value) => {
  if (value == null) return '0.00'
  return new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

const formatNumber = (value) => {
  if (value == null) return '0'
  return new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(value)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString + 'T00:00:00')
  return date.toLocaleDateString('es-AR')
}

const loadDetalle = async () => {
  if (!props.numeroComprobante) return

  loading.value = true
  error.value = null
  detalle.value = null

  try {
    // Sanitizar número de comprobante: en algunos entornos puede venir con sufijos
    // como ":1" (línea). Eliminamos cualquier ":<digits>" al final antes de pedir el detalle.
    const originalNumero = props.numeroComprobante?.toString()
    const numeroSanitizado = originalNumero ? originalNumero.replace(/:\d+$/, '') : originalNumero
    // Guardar info de depuración visible en UI (útil cuando la consola está silenciada en producción)
    debugInfo.value = { originalNumero, numeroSanitizado, when: new Date().toISOString() }
    console.debug?.('[DetalleComprobanteModal] solicitando detalle para', { originalNumero, numeroSanitizado })

    const response = await getDetalleComprobante(numeroSanitizado)
    detalle.value = response
    // Añadir respuesta al debug
    debugInfo.value = { ...debugInfo.value, response }
  } catch (err) {
    console.error('Error al cargar detalle:', err)
    // Mejor mensaje de error para producción: incluir el número solicitado
    const requested = props.numeroComprobante
    const serverMsg = err.response?.data?.message || err.response?.data?.error || err.message
    error.value = `No se pudo obtener detalle para ${requested}: ${serverMsg}`
    // Añadir error al debug
    debugInfo.value = { ...debugInfo.value, error: serverMsg, status: err.response?.status }
  } finally {
    loading.value = false
  }
}

// Watchers
watch(
  () => props.modelValue && props.numeroComprobante,
  (shouldLoad) => {
    if (shouldLoad) {
      loadDetalle()
    }
  },
  { immediate: true }
)

// Limpiar datos cuando se cierra el modal
watch(
  () => props.modelValue,
  (isOpen) => {
    if (!isOpen) {
      detalle.value = null
      error.value = null
    }
  }
)
</script>