<template>
  <aside class="sticky top-4 hidden self-start xl:block">
    <div
      class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-all"
      :class="collapsed ? 'w-[68px]' : 'w-full'"
    >
      <button
        v-if="collapsed"
        type="button"
        class="flex min-h-[180px] w-full flex-col items-center gap-3 px-2 py-4 text-gray-700 hover:bg-gray-50"
        title="Abrir pedido"
        @click="setCollapsed(false)"
      >
        <span class="flex h-10 w-10 items-center justify-center rounded-full bg-red-600 text-sm font-black text-white">{{ cart.totalItems }}</span>
        <span class="text-xs font-black uppercase [writing-mode:vertical-rl]">Tu pedido</span>
        <span class="text-lg">‹</span>
      </button>

      <template v-else>
        <header class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <div class="flex items-center gap-2">
            <h2 class="font-black text-gray-950">Tu pedido</h2>
            <span class="rounded-full bg-red-600 px-2 py-0.5 text-xs font-black text-white">{{ cart.totalItems }}</span>
          </div>
          <button
            type="button"
            class="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-900"
            aria-label="Ocultar carrito"
            title="Ocultar carrito"
            @click="setCollapsed(true)"
          >
            ›
          </button>
        </header>

        <div v-if="cart.items.length === 0" class="px-5 py-10 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-2xl">🛒</div>
          <p class="mt-3 font-bold text-gray-900">Todavía no agregaste productos</p>
          <p class="mt-1 text-sm text-gray-500">Elegí cantidades desde el catálogo y aparecerán acá.</p>
        </div>

        <div v-else>
          <div class="max-h-[48vh] divide-y divide-gray-100 overflow-y-auto">
            <article v-for="item in cart.items" :key="item.articulo.clave" class="p-4">
              <div class="flex gap-3">
                <img
                  class="h-12 w-12 flex-shrink-0 rounded-lg border border-gray-200 bg-white object-contain p-1"
                  :src="item.articulo.imagen || '/placeholder.png'"
                  :alt="item.articulo.nombre"
                >
                <div class="min-w-0 flex-1">
                  <p class="line-clamp-2 text-sm font-bold text-gray-950">{{ item.articulo.nombre }}</p>
                  <p class="mt-0.5 text-xs font-semibold text-gray-500">Clave {{ item.articulo.clave }}</p>
                </div>
                <button
                  type="button"
                  class="self-start rounded-md p-1.5 text-red-600 hover:bg-red-50"
                  :aria-label="`Eliminar ${item.articulo.nombre}`"
                  @click="cart.remove(item.articulo.clave)"
                >
                  ×
                </button>
              </div>

              <div class="mt-3 flex items-end justify-between gap-3">
                <div>
                  <div class="grid w-32 grid-cols-[36px_1fr_36px] overflow-hidden rounded-lg border border-gray-300 bg-white">
                    <button type="button" class="h-9 font-black hover:bg-gray-100" @click="decrement(item)">−</button>
                    <input
                      type="number"
                      :min="stepFor(item)"
                      :step="stepFor(item)"
                      :value="item.cantidad"
                      class="h-9 w-full border-x border-gray-200 text-center text-sm font-black focus:outline-none"
                      @change="setQuantity(item, $event.target.value)"
                    >
                    <button type="button" class="h-9 font-black hover:bg-gray-100" @click="increment(item)">+</button>
                  </div>
                  <p v-if="isM2(item)" class="mt-1 text-[11px] font-semibold text-gray-500">{{ boxLabel(item) }}</p>
                </div>
                <p class="pb-2 text-right text-sm font-black text-gray-950">$ {{ money(item.subtotal) }}</p>
              </div>
            </article>
          </div>

          <button type="button" class="mx-4 my-3 text-xs font-bold text-red-700 hover:underline" @click="cart.clear()">Vaciar carrito</button>

          <div class="border-t border-gray-200 bg-gray-50 p-4">
            <div class="space-y-2 text-sm">
              <div class="flex justify-between text-gray-600">
                <span>{{ cart.totalItems }} artículo{{ cart.totalItems === 1 ? '' : 's' }}</span>
                <span class="font-semibold">{{ weightLabel }} kg</span>
              </div>
              <div class="flex items-end justify-between gap-3">
                <span class="font-bold text-gray-700">Total estimado</span>
                <span class="text-xl font-black text-red-700">$ {{ money(cart.totalPrice) }}</span>
              </div>
            </div>

            <div class="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              <strong>No se realiza pago online.</strong> Ventas confirmará disponibilidad, precio final y condiciones.
            </div>

            <RouterLink
              to="/revisar-pedido"
              class="mt-4 flex w-full items-center justify-center rounded-lg bg-red-600 px-4 py-3 text-sm font-black text-white shadow-sm transition hover:bg-red-700"
            >
              Revisar pedido →
            </RouterLink>
          </div>
        </div>
      </template>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { cart } from '@/services/cart'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
})

const emit = defineEmits(['update:collapsed'])

const setCollapsed = (value) => {
  localStorage.setItem('order_sidebar_collapsed', value ? '1' : '0')
  emit('update:collapsed', value)
}

const money = (value) => new Intl.NumberFormat('es-AR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(Number(value) || 0)

const isM2 = (item) => (item.articulo.campoa1 || '').toLowerCase() === 'a' && Number(item.articulo.mts2) > 0
const stepFor = (item) => isM2(item) ? Number(item.articulo.mts2) : 1

const normalizeQuantity = (item, value) => {
  const step = stepFor(item)
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return step
  if (isM2(item)) return Number((Math.max(step, Math.ceil(parsed / step) * step)).toFixed(3))
  return Math.max(1, parsed)
}

const setQuantity = (item, value) => cart.updateQuantity(item.articulo.clave, normalizeQuantity(item, value))
const increment = (item) => setQuantity(item, Number(item.cantidad) + stepFor(item))
const decrement = (item) => setQuantity(item, Math.max(stepFor(item), Number(item.cantidad) - stepFor(item)))

const boxLabel = (item) => {
  const step = stepFor(item)
  const cajas = Math.round(Number(item.cantidad) / step)
  return `${cajas} caja${cajas === 1 ? '' : 's'} · ${step} m²/caja`
}

const totalWeight = computed(() => cart.items.reduce((total, item) => {
  const peso = Number(item.articulo.peso) || 0
  if (isM2(item)) {
    return total + ((Number(item.cantidad) / stepFor(item)) * peso)
  }
  return total + (Number(item.cantidad) * peso)
}, 0))

const weightLabel = computed(() => new Intl.NumberFormat('es-AR', {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
}).format(totalWeight.value))
</script>
