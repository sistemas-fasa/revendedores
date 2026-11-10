<template>
  <span
    class="stock-badge"
    :class="[`stock-badge--${estado}`, { 'stock-badge--full': full }]"
    :title="tooltip"
  >
    <span class="stock-badge__dot" aria-hidden="true"></span>
    <span class="stock-badge__label">{{ etiqueta }}</span>
    <span v-if="mostrarCantidad" class="stock-badge__qty">{{ cantidadFmt }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  estado: { type: String, default: 'sin_datos' },
  stock: { type: [Number, String, null], default: null },
  minimo: { type: [Number, String, null], default: null },
  descuentaDe: { type: String, default: '' },
  full: { type: Boolean, default: false },
})

const cantidad = computed(() => {
  const n = parseFloat(props.stock)
  return Number.isFinite(n) ? n : null
})

const mostrarCantidad = computed(() => cantidad.value !== null)

const cantidadFmt = computed(() => {
  if (cantidad.value === null) return ''
  const opts = Number.isInteger(cantidad.value)
    ? { maximumFractionDigits: 0 }
    : { minimumFractionDigits: 0, maximumFractionDigits: 2 }
  return cantidad.value.toLocaleString('es-AR', opts)
})

const etiquetas = {
  verde: 'En stock',
  amarillo: 'Stock bajo',
  rojo: 'Sin stock',
  sin_datos: 'Stock s/d',
}

const etiqueta = computed(() => etiquetas[props.estado] || etiquetas.sin_datos)

const tooltip = computed(() => {
  const base = `${etiqueta.value}${mostrarCantidad.value ? `: ${cantidadFmt.value}` : ''}`
  const min = parseFloat(props.minimo)
  const conMin = Number.isFinite(min) ? ` (mín. ${min})` : ''
  const padre = props.descuentaDe ? ` · descuenta de ${props.descuentaDe}` : ''
  return `${base}${conMin}${padre}`
})
</script>

<style scoped>
.stock-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 9999px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.4;
  border: 1px solid transparent;
  white-space: nowrap;
}
.stock-badge--full {
  width: 100%;
  justify-content: center;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
}
.stock-badge__dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: currentColor;
  flex-shrink: 0;
}
.stock-badge--verde { background: #dcfce7; color: #166534; border-color: #86efac; }
.stock-badge--amarillo { background: #fef9c3; color: #854d0e; border-color: #fde047; }
.stock-badge--rojo { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
.stock-badge--sin_datos { background: #f3f4f6; color: #6b7280; border-color: #e5e7eb; }
.stock-badge__qty { font-weight: 800; }
</style>
