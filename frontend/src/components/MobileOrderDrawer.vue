<template>
  <div class="xl:hidden">
    <button
      type="button"
      class="fixed inset-x-3 bottom-3 z-10 flex items-center justify-between rounded-xl bg-red-600 px-4 py-3 text-white shadow-2xl"
      @click="openDrawer"
    >
      <span class="flex items-center gap-2 font-black">
        <span class="flex h-8 min-w-8 items-center justify-center rounded-full bg-white px-2 text-sm text-red-700">{{ cart.totalItems }}</span>
        Ver pedido
      </span>
      <span class="text-sm font-black">$ {{ money(cart.totalPrice) }}</span>
    </button>

    <div
      v-if="open"
      class="fixed inset-0 z-40 bg-black/45"
      aria-hidden="true"
      @click="closeDrawer"
    ></div>

    <section
      v-if="open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="mobile-order-title"
      class="fixed inset-x-0 bottom-0 z-50 max-h-[88vh] overflow-hidden rounded-t-2xl bg-white shadow-2xl"
    >
      <header class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div>
          <p id="mobile-order-title" class="font-black text-gray-950">Tu pedido</p>
          <p class="text-xs font-semibold text-gray-500">{{ cart.totalItems }} artículo{{ cart.totalItems === 1 ? '' : 's' }}</p>
        </div>
        <button ref="closeButton" type="button" class="rounded-lg p-2 text-xl font-bold text-gray-600 hover:bg-gray-100" aria-label="Cerrar pedido" @click="closeDrawer">×</button>
      </header>

      <div v-if="cart.items.length === 0" class="px-5 py-12 text-center">
        <p class="font-bold text-gray-900">Tu pedido está vacío</p>
        <p class="mt-1 text-sm text-gray-500">Agregá productos desde el catálogo.</p>
      </div>

      <template v-else>
        <div class="max-h-[55vh] divide-y divide-gray-100 overflow-y-auto overscroll-contain">
          <article v-for="item in cart.items" :key="item.articulo.clave" class="p-4">
            <div class="flex gap-3">
              <img class="h-12 w-12 rounded-lg border border-gray-200 object-contain p-1" :src="item.articulo.imagen || '/placeholder.png'" :alt="item.articulo.nombre">
              <div class="min-w-0 flex-1">
                <p class="line-clamp-2 text-sm font-bold text-gray-950">{{ item.articulo.nombre }}</p>
                <p class="text-xs font-semibold text-gray-500">{{ item.articulo.clave }}</p>
              </div>
              <button type="button" class="self-start rounded-md p-2 text-red-600 hover:bg-red-50" :aria-label="`Eliminar ${item.articulo.nombre}`" @click="cart.remove(item.articulo.clave)">×</button>
            </div>

            <div class="mt-3 flex items-end justify-between gap-3">
              <div>
                <div class="grid w-36 grid-cols-[40px_1fr_40px] overflow-hidden rounded-lg border border-gray-300">
                  <button type="button" class="h-11 text-lg font-black hover:bg-gray-100" @click="decrement(item)">−</button>
                  <input type="number" :min="stepFor(item)" :step="stepFor(item)" :value="item.cantidad" class="h-11 w-full border-x border-gray-200 text-center text-base font-black focus:outline-none" @change="setQuantity(item, $event.target.value)">
                  <button type="button" class="h-11 text-lg font-black hover:bg-gray-100" @click="increment(item)">+</button>
                </div>
                <p v-if="isM2(item)" class="mt-1 text-[11px] font-semibold text-gray-500">{{ boxLabel(item) }}</p>
              </div>
              <p class="pb-2 text-sm font-black text-gray-950">$ {{ money(item.subtotal) }}</p>
            </div>
          </article>
        </div>

        <footer class="border-t border-gray-200 bg-gray-50 p-4 pb-[calc(1rem+env(safe-area-inset-bottom))]">
          <div class="flex items-end justify-between gap-4">
            <div>
              <p class="text-xs font-semibold text-gray-500">Peso estimado</p>
              <p class="text-sm font-bold text-gray-800">{{ weightLabel }} kg</p>
            </div>
            <div class="text-right">
              <p class="text-xs font-semibold text-gray-500">Total estimado</p>
              <p class="text-xl font-black text-red-700">$ {{ money(cart.totalPrice) }}</p>
            </div>
          </div>

          <p class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900"><strong>No se realiza pago online.</strong> Ventas confirmará disponibilidad y condiciones.</p>

          <div class="mt-3 grid grid-cols-[auto_1fr] gap-2">
            <button type="button" class="rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-bold text-gray-700" @click="cart.clear()">Vaciar</button>
            <RouterLink to="/revisar-pedido" class="flex items-center justify-center rounded-lg bg-red-600 px-4 py-3 text-sm font-black text-white" @click="closeDrawer">Revisar pedido →</RouterLink>
          </div>
        </footer>
      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { cart } from '@/services/cart'

const open = ref(false)
const closeButton = ref(null)

const money = (value) => new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value) || 0)
const isM2 = (item) => (item.articulo.campoa1 || '').toLowerCase() === 'a' && Number(item.articulo.mts2) > 0
const stepFor = (item) => isM2(item) ? Number(item.articulo.mts2) : 1
const normalize = (item, value) => {
  const step = stepFor(item)
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return step
  if (isM2(item)) return Number((Math.max(step, Math.ceil(parsed / step) * step)).toFixed(3))
  return Math.max(1, parsed)
}
const setQuantity = (item, value) => cart.updateQuantity(item.articulo.clave, normalize(item, value))
const increment = (item) => setQuantity(item, Number(item.cantidad) + stepFor(item))
const decrement = (item) => setQuantity(item, Math.max(stepFor(item), Number(item.cantidad) - stepFor(item)))
const boxLabel = (item) => {
  const step = stepFor(item)
  const boxes = Math.round(Number(item.cantidad) / step)
  return `${boxes} caja${boxes === 1 ? '' : 's'} · ${step} m²/caja`
}

const totalWeight = computed(() => cart.items.reduce((total, item) => {
  const peso = Number(item.articulo.peso) || 0
  return total + (isM2(item) ? (Number(item.cantidad) / stepFor(item)) * peso : Number(item.cantidad) * peso)
}, 0))
const weightLabel = computed(() => new Intl.NumberFormat('es-AR', { minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(totalWeight.value))

const openDrawer = async () => {
  open.value = true
  document.body.style.overflow = 'hidden'
  await nextTick()
  closeButton.value?.focus()
}
const closeDrawer = () => {
  open.value = false
  document.body.style.overflow = ''
}
const onKeydown = (event) => {
  if (event.key === 'Escape' && open.value) closeDrawer()
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>
