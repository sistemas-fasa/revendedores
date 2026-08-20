<template>
  <div v-if="open" class="fixed inset-0 z-[70] flex items-start justify-center bg-black/45 p-3 pt-[8vh] sm:p-6 sm:pt-[10vh]" @click.self="close">
    <section role="dialog" aria-modal="true" aria-labelledby="quick-load-title" class="w-full max-w-xl overflow-hidden rounded-2xl bg-white shadow-2xl">
      <header class="flex items-start justify-between gap-4 border-b border-gray-200 px-5 py-4">
        <div>
          <p class="text-xs font-black uppercase tracking-wide text-red-700">Carga rápida</p>
          <h2 id="quick-load-title" class="mt-1 text-xl font-black text-gray-950">Agregar por código</h2>
          <p class="mt-1 text-sm text-gray-500">Código → Enter → cantidad → Enter. Repetí sin usar el mouse.</p>
        </div>
        <button type="button" class="rounded-lg p-2 text-xl font-black text-gray-500 hover:bg-gray-100" aria-label="Cerrar carga rápida" @click="close">×</button>
      </header>

      <div class="space-y-4 p-5">
        <label class="block">
          <span class="text-sm font-bold text-gray-800">Código / clave / descripción</span>
          <div class="mt-1 flex gap-2">
            <input
              ref="codeInput"
              v-model.trim="query"
              type="text"
              autocomplete="off"
              class="h-12 min-w-0 flex-1 rounded-lg border border-gray-300 px-4 text-base font-bold text-gray-950 shadow-sm focus:border-red-600 focus:outline-none focus:ring-4 focus:ring-red-100"
              placeholder="Ej: .030011"
              @keydown.enter.prevent="resolveArticle"
            >
            <button type="button" class="rounded-lg bg-gray-900 px-4 text-sm font-black text-white disabled:opacity-50" :disabled="loading || !query" @click="resolveArticle">
              {{ loading ? 'Buscando…' : 'Buscar' }}
            </button>
          </div>
        </label>

        <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-800">{{ error }}</div>

        <div v-if="article" class="rounded-xl border border-gray-200 bg-gray-50 p-4">
          <div class="flex gap-3">
            <img class="h-14 w-14 rounded-lg border border-gray-200 bg-white object-contain p-1" :src="article.imagen || '/placeholder.png'" :alt="article.nombre">
            <div class="min-w-0 flex-1">
              <p class="font-black text-gray-950">{{ article.nombre }}</p>
              <p class="mt-0.5 text-xs font-semibold text-gray-500">Clave {{ article.clave }} · {{ article.unidad || 'UN' }}</p>
              <p class="mt-2 text-lg font-black text-red-700">$ {{ money(article.precio_lista) }}</p>
            </div>
          </div>

          <div class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
            <label>
              <span class="text-sm font-bold text-gray-800">Cantidad</span>
              <input
                ref="quantityInput"
                :value="quantity"
                type="number"
                :min="step"
                :step="step"
                class="mt-1 h-12 w-full rounded-lg border border-gray-300 px-4 text-lg font-black text-gray-950 focus:border-red-600 focus:outline-none focus:ring-4 focus:ring-red-100"
                @input="setQuantity($event.target.value)"
                @keydown.enter.prevent="addAndContinue"
              >
            </label>
            <button type="button" class="h-12 rounded-lg bg-red-600 px-5 text-sm font-black text-white hover:bg-red-700" @click="addAndContinue">Agregar y seguir</button>
          </div>

          <p class="mt-2 text-xs font-semibold text-gray-500">
            <template v-if="isM2">{{ boxes }} caja{{ boxes === 1 ? '' : 's' }} · {{ step }} m²/caja.</template>
            <template v-else>Cantidad mínima: 1.</template>
            Si el producto ya está en el pedido, esta carga se suma a la cantidad existente.
          </p>
        </div>

        <div class="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-900">
          La condición de pago, modalidad e impuestos son los seleccionados actualmente en la home. El backend seguirá recalculando el precio final de forma autoritativa.
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import api from '@/services/api'
import { cart } from '@/services/cart'

const props = defineProps({
  open: { type: Boolean, default: false },
  modalidad: { type: String, default: 'retira' },
  conImpuestos: { type: Boolean, default: true },
  condicionPago: { type: [String, Number], default: '' },
})
const emit = defineEmits(['update:open', 'added'])

const query = ref('')
const article = ref(null)
const quantity = ref(1)
const loading = ref(false)
const error = ref('')
const codeInput = ref(null)
const quantityInput = ref(null)

const money = (value) => new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value) || 0)
const isM2 = computed(() => (article.value?.campoa1 || '').toLowerCase() === 'a' && Number(article.value?.mts2) > 0)
const step = computed(() => isM2.value ? Number(article.value.mts2) : 1)
const boxes = computed(() => isM2.value ? Math.round(Number(quantity.value) / step.value) : 0)

const normalizeQuantity = (value) => {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return step.value
  if (isM2.value) return Number((Math.max(step.value, Math.ceil(parsed / step.value) * step.value)).toFixed(3))
  return Math.max(1, parsed)
}
const setQuantity = (value) => { quantity.value = normalizeQuantity(value) }

const focusCode = async () => {
  await nextTick()
  codeInput.value?.focus()
  codeInput.value?.select?.()
}

const resolveArticle = async () => {
  if (!query.value || loading.value) return
  loading.value = true
  error.value = ''
  article.value = null
  try {
    const response = await api.get('/api/articulos/', {
      params: {
        search: query.value,
        page: 1,
        page_size: 10,
        modalidad: props.modalidad,
        con_impuestos: props.conImpuestos,
        condicion_pago: props.condicionPago,
      },
    })
    const results = response.data?.results || []
    const normalized = query.value.trim().toLowerCase()
    const match = results.find(item => String(item.clave).trim().toLowerCase() === normalized) || results[0]
    if (!match) {
      error.value = `No se encontró ningún artículo para “${query.value}”.`
      await focusCode()
      return
    }

    let resolved = { ...match }
    if (!resolved.precio_lista || !resolved.mostrar_precio) {
      const priceResponse = await api.post('/api/consultar-precio/', {
        articulo_clave: resolved.clave,
        modalidad: props.modalidad,
        con_impuestos: props.conImpuestos,
        condicion_pago: props.condicionPago,
      })
      if (!priceResponse.data?.success || priceResponse.data?.articulo?.precio_lista == null) {
        throw new Error('No hay precio disponible para este artículo.')
      }
      resolved = { ...resolved, ...priceResponse.data.articulo, mostrar_precio: true }
    }

    article.value = resolved
    quantity.value = (resolved.campoa1 || '').toLowerCase() === 'a' && Number(resolved.mts2) > 0 ? Number(resolved.mts2) : 1
    await nextTick()
    quantityInput.value?.focus()
    quantityInput.value?.select?.()
  } catch (exc) {
    error.value = exc.response?.data?.detail || exc.response?.data?.error || exc.message || 'No se pudo resolver el artículo.'
    await focusCode()
  } finally {
    loading.value = false
  }
}

const addAndContinue = async () => {
  if (!article.value) return
  const amount = normalizeQuantity(quantity.value)
  const existing = cart.items.find(item => item.articulo.clave === article.value.clave)
  if (existing) cart.updateQuantity(article.value.clave, Number(existing.cantidad) + amount)
  else cart.add(article.value, amount)
  emit('added', `${article.value.nombre}: ${amount} agregado al pedido`)
  query.value = ''
  article.value = null
  quantity.value = 1
  error.value = ''
  await focusCode()
}

const close = () => emit('update:open', false)

watch(() => props.open, async (value) => {
  if (value) {
    query.value = ''
    article.value = null
    error.value = ''
    await focusCode()
  }
})
</script>
