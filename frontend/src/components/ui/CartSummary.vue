<template>
  <aside class="cart-summary sticky top-20 rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
    <div class="space-y-4">
      <div class="cart-summary-total rounded-lg bg-red-50 px-4 py-3">
        <p class="text-xs font-bold uppercase text-red-700">Total estimado</p>
        <p class="mt-1 text-3xl font-black text-gray-950">$ {{ total }}</p>
      </div>

      <div class="grid grid-cols-2 gap-3 text-sm">
        <div class="rounded-lg border border-gray-200 bg-gray-50 p-3">
          <p class="text-xs font-semibold uppercase text-gray-500">Artículos</p>
          <p class="text-lg font-bold text-gray-950">{{ itemsCount }}</p>
        </div>
        <div class="rounded-lg border border-gray-200 bg-gray-50 p-3">
          <p class="text-xs font-semibold uppercase text-gray-500">Peso total</p>
          <p class="text-lg font-bold text-gray-950">{{ totalWeight }} kg</p>
        </div>
      </div>

      <div class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm leading-5 text-amber-950">
        <p class="font-bold">Precio sujeto a confirmación</p>
        <p class="mt-1">Ventas revisará bonificaciones, descuentos por cantidad y disponibilidad antes de cerrar el pedido.</p>
      </div>

      <button
        type="button"
        :disabled="disabled || loading"
        class="cart-summary-cta inline-flex w-full items-center justify-center gap-2 rounded-lg border border-red-700 bg-red-700 px-5 py-4 text-base font-black text-white shadow-lg shadow-red-900/20 transition hover:border-red-800 hover:bg-red-800 focus:outline-none focus:ring-4 focus:ring-red-200 disabled:cursor-not-allowed disabled:border-gray-300 disabled:bg-gray-300 disabled:text-gray-600 disabled:shadow-none"
        @click="$emit('checkout')"
      >
        <span v-if="loading" class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
        <span>{{ loading ? loadingLabel : 'Confirmar pedido' }}</span>
      </button>

      <p class="text-center text-xs font-semibold text-gray-500">No se envía nada hasta presionar confirmar.</p>
    </div>
  </aside>
</template>

<script setup>
defineEmits(['checkout'])

defineProps({
  total: { type: String, required: true },
  totalWeight: { type: String, required: true },
  itemsCount: { type: Number, required: true },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  loadingLabel: { type: String, default: 'Procesando pedido...' },
})
</script>

<style scoped>
.cart-summary {
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.09);
}

.cart-summary-total {
  border: 1px solid #fbd5d5;
  background:
    linear-gradient(135deg, rgba(253, 232, 232, 0.95), rgba(255, 255, 255, 0.8)),
    #fff;
}

.cart-summary-cta {
  min-height: 54px;
  letter-spacing: 0;
}
</style>
