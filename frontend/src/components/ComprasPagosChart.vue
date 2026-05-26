<template>
  <div class="bg-white backdrop-blur-sm rounded-2xl shadow-lg border border-gray-300 p-6 sm:p-8 transition-all hover:shadow-xl w-full">
    <h3 class="text-xl sm:text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
      <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
      Compras vs Pagos (últimos 12 meses)
    </h3>

    <div class="w-full" style="height: 320px;">
      <canvas ref="canvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'
import { getComprobantesCliente } from '@/services/dashboard'

Chart.register(...registerables)

const canvas = ref(null)
let chartInstance = null

const buildMonths = (months = 12) => {
  const labels = []
  const date = new Date()
  // Start from oldest month
  date.setDate(1)
  date.setMonth(date.getMonth() - (months - 1))

  for (let i = 0; i < months; i++) {
    labels.push(new Intl.DateTimeFormat('es-ES', { month: 'short', year: '2-digit' }).format(new Date(date)))
    date.setMonth(date.getMonth() + 1)
  }

  return labels
}

const computeDateRange = (months = 12) => {
  const end = new Date()
  const start = new Date()
  start.setDate(1)
  start.setMonth(start.getMonth() - (months - 1))

  const pad = (n) => n.toString().padStart(2, '0')
  const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

  return { desde: fmt(start), hasta: fmt(end) }
}

const prepareChart = (labels, compras, pagos) => {
  const ctx = canvas.value.getContext('2d')
  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Compras (F + D)',
          data: compras,
          borderColor: '#fb923c',
          backgroundColor: 'rgba(251,146,60,0.15)',
          fill: true,
          tension: 0.25,
          pointRadius: 3,
          pointBackgroundColor: '#fb923c',
          pointBorderColor: '#fff',
        },
        {
          label: 'Pagos y Créditos (R + C)',
          data: pagos,
          borderColor: '#34d399',
          backgroundColor: 'rgba(52,211,153,0.12)',
          fill: true,
          tension: 0.25,
          pointRadius: 3,
          pointBackgroundColor: '#34d399',
          pointBorderColor: '#fff',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'top' },
        tooltip: {
          callbacks: {
            label: function(context) {
              const v = context.parsed.y ?? context.parsed
              return `${context.dataset.label}: $${new Intl.NumberFormat('es-AR', {minimumFractionDigits:2}).format(v)}`
            }
          }
        }
      },
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '$' + new Intl.NumberFormat('es-AR', {minimumFractionDigits:0}).format(value)
            }
          }
        }
      }
    }
  })
}

onMounted(async () => {
  const months = 12
  const labels = buildMonths(months)
  const { desde, hasta } = computeDateRange(months)

  try {
    // Pedimos todos los comprobantes en el rango con page_size grande
    const resp = await getComprobantesCliente({ fecha_desde: desde, fecha_hasta: hasta, page_size: 1000 })
    if (!resp || !resp.success) {
      console.error('No se obtuvieron comprobantes para el gráfico', resp)
      prepareChart(labels, new Array(months).fill(0), new Array(months).fill(0))
      return
    }

    const items = resp.data || []

    // Inicializar arrays
    const compras = new Array(months).fill(0)
    const pagos = new Array(months).fill(0)

    // Fecha de inicio para calcular índice
    const start = new Date()
    start.setDate(1)
    start.setMonth(start.getMonth() - (months - 1))

    for (const c of items) {
      if (!c.fecha) continue
      const d = new Date(c.fecha + 'T00:00:00')
      const index = (d.getFullYear() - start.getFullYear()) * 12 + (d.getMonth() - start.getMonth())
      if (index < 0 || index >= months) continue

      if (['F', 'D'].includes(c.codigo)) {
        compras[index] += Number(c.total || 0)
      } else if (['R', 'C'].includes(c.codigo)) {
        // Usar valor absoluto para pagos/creditos (pueden venir como negativos)
        pagos[index] += Math.abs(Number(c.total || 0))
      }
    }

    prepareChart(labels, compras, pagos)
  } catch (e) {
    console.error('Error al preparar gráfico:', e)
    prepareChart(buildMonths(12), new Array(12).fill(0), new Array(12).fill(0))
  }
})

onBeforeUnmount(() => {
  if (chartInstance) chartInstance.destroy()
})
</script>

<style scoped>
canvas { max-height: 320px; }
</style>
