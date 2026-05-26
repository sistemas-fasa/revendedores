<template>
  <section class="space-y-6">
    <header class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase text-red-600">Staff</p>
        <h1 class="text-2xl font-semibold text-gray-900">Reporte Bot</h1>
        <p class="mt-1 text-sm text-gray-500">Resumen tecnico de conversaciones y calidad de respuestas.</p>
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-600" for="days">Periodo</label>
        <select id="days" v-model="days" class="rounded border border-gray-300 px-3 py-2 text-sm" @change="loadReport">
          <option :value="1">24 horas</option>
          <option :value="7">7 dias</option>
          <option :value="30">30 dias</option>
          <option :value="90">90 dias</option>
        </select>
        <button class="rounded bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700" @click="loadReport">
          Actualizar
        </button>
      </div>
    </header>

    <div v-if="loading" class="rounded border border-gray-200 bg-white p-4 text-sm text-gray-600">Cargando reporte...</div>
    <div v-if="error" class="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</div>

    <template v-if="!loading && !error">
      <div class="grid gap-4 md:grid-cols-4">
        <div class="rounded border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-sm text-gray-500">Mensajes</p>
          <p class="mt-2 text-3xl font-bold text-gray-900">{{ report.total_messages || 0 }}</p>
        </div>
        <div class="rounded border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-sm text-gray-500">OK</p>
          <p class="mt-2 text-3xl font-bold text-green-700">{{ countStatus('ok') }}</p>
        </div>
        <div class="rounded border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-sm text-gray-500">Ambiguos</p>
          <p class="mt-2 text-3xl font-bold text-amber-600">{{ countStatus('ambiguous') }}</p>
        </div>
        <div class="rounded border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-sm text-gray-500">No entendidos</p>
          <p class="mt-2 text-3xl font-bold text-gray-700">{{ countStatus('fallback') + countStatus('not_found') }}</p>
        </div>
      </div>

      <div class="grid gap-4 lg:grid-cols-3">
        <SummaryBox title="Origen" :items="report.by_origin" />
        <SummaryBox title="Intencion" :items="report.by_intention" />
        <SummaryBox title="Estado" :items="report.by_status" />
      </div>

      <div class="rounded border border-gray-200 bg-white p-4 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-gray-900">Recomendaciones</h2>
        <ul class="space-y-2 text-sm text-gray-700">
          <li v-for="item in report.recommendations || []" :key="item" class="rounded bg-gray-50 px-3 py-2">
            {{ item }}
          </li>
        </ul>
      </div>

      <div class="rounded border border-gray-200 bg-white shadow-sm">
        <div class="border-b border-gray-200 px-4 py-3">
          <h2 class="text-lg font-semibold text-gray-900">Ultimos mensajes</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[900px] text-left text-sm">
            <thead class="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3">Origen</th>
                <th class="px-4 py-3">Usuario</th>
                <th class="px-4 py-3">Intencion</th>
                <th class="px-4 py-3">Estado</th>
                <th class="px-4 py-3">Mensaje</th>
                <th class="px-4 py-3">Respuesta</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in report.recent || []" :key="row.id" class="border-t border-gray-100">
                <td class="px-4 py-3 text-gray-500">{{ formatDate(row.fecha_hora) }}</td>
                <td class="px-4 py-3">{{ row.origen }}</td>
                <td class="px-4 py-3">{{ row.usuario || row.telefono || '-' }}</td>
                <td class="px-4 py-3">{{ row.intencion }}</td>
                <td class="px-4 py-3">
                  <span class="rounded px-2 py-1 text-xs font-semibold" :class="statusClass(row.estado)">
                    {{ row.estado }}
                  </span>
                </td>
                <td class="max-w-xs px-4 py-3 text-gray-700">{{ row.mensaje_usuario }}</td>
                <td class="max-w-sm whitespace-pre-line px-4 py-3 text-gray-700">{{ row.respuesta_bot }}</td>
              </tr>
              <tr v-if="!report.recent?.length">
                <td colspan="7" class="px-4 py-6 text-center text-gray-500">Sin logs en el periodo seleccionado.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { h, onMounted, ref } from 'vue'
import api from '@/services/api'

const days = ref(7)
const loading = ref(false)
const error = ref('')
const report = ref({})

const loadReport = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get('/api/staff/bot/report/', { params: { days: days.value } })
    report.value = response.data
  } catch (err) {
    console.error(err)
    error.value = 'No se pudo cargar el reporte del bot.'
  } finally {
    loading.value = false
  }
}

const countStatus = (status) => Number(report.value.by_status?.[status] || 0)

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

const statusClass = (status) => {
  if (status === 'ok') return 'bg-green-50 text-green-700'
  if (status === 'ambiguous') return 'bg-amber-50 text-amber-700'
  if (status === 'error') return 'bg-red-50 text-red-700'
  return 'bg-gray-100 text-gray-700'
}

const SummaryBox = {
  props: {
    title: { type: String, required: true },
    items: { type: Object, default: () => ({}) }
  },
  setup(props) {
    return () => h('div', { class: 'rounded border border-gray-200 bg-white p-4 shadow-sm' }, [
      h('h2', { class: 'mb-3 text-lg font-semibold text-gray-900' }, props.title),
      ...Object.entries(props.items || {}).map(([key, value]) =>
        h('div', { class: 'flex justify-between border-t border-gray-100 py-2 text-sm' }, [
          h('span', { class: 'text-gray-600' }, key),
          h('strong', { class: 'text-gray-900' }, String(value))
        ])
      ),
      !Object.keys(props.items || {}).length ? h('p', { class: 'text-sm text-gray-500' }, 'Sin datos') : null
    ])
  }
}

onMounted(loadReport)
</script>
