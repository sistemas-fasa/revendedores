<template>
  <aside class="ui-panel sticky top-20 p-5">
    <div class="space-y-4">
      <div>
        <p class="text-sm font-semibold text-gray-500">Total estimado</p>
        <p class="mt-1 text-3xl font-black text-gray-950">$ {{ total }}</p>
      </div>

      <div class="grid grid-cols-2 gap-3 text-sm">
        <div class="rounded-lg bg-gray-50 p-3">
          <p class="text-gray-500">Items</p>
          <p class="text-lg font-bold text-gray-950">{{ itemsCount }}</p>
        </div>
        <div class="rounded-lg bg-gray-50 p-3">
          <p class="text-gray-500">Peso total</p>
          <p class="text-lg font-bold text-gray-950">{{ totalWeight }} kg</p>
        </div>
      </div>

      <div class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm leading-5 text-amber-900">
        El precio es orientativo. Ventas confirmará bonificaciones, descuentos por cantidad y disponibilidad.
      </div>

      <button
        type="button"
        :disabled="disabled || loading"
        class="ui-button ui-button-primary w-full px-5 py-3 text-base disabled:cursor-not-allowed disabled:opacity-60"
        @click="$emit('checkout')"
      >
        <span v-if="loading" class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
        <span>{{ loading ? loadingLabel : 'Confirmar pedido' }}</span>
      </button>
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
