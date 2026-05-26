<template>
  <div class="p-6">
    <h2 class="text-2xl font-semibold mb-4">Tracking - Campañas</h2>

    <div class="mb-4 flex items-center gap-4">
      <label class="font-medium">Campaña:</label>
      <select v-model="selectedCampaign" @change="onCampaignChange" class="border rounded px-3 py-1">
        <option v-for="c in campaigns" :key="c.campaign" :value="c.campaign">{{ c.campaign }} ({{ c.count }})</option>
      </select>
    </div>

    <div v-if="loading" class="text-gray-600">Cargando...</div>

    <div v-if="!loading && selectedCampaign">
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="p-4 bg-white shadow rounded">
          <div class="text-sm text-gray-500">Aperturas totales</div>
          <div class="text-2xl font-bold">{{ kpis.total_opens }}</div>
        </div>
        <div class="p-4 bg-white shadow rounded">
          <div class="text-sm text-gray-500">Emails únicos</div>
          <div class="text-2xl font-bold">{{ kpis.unique_emails }}</div>
        </div>
        <div class="p-4 bg-white shadow rounded">
          <div class="text-sm text-gray-500">IPs únicas</div>
          <div class="text-2xl font-bold">{{ kpis.unique_ips }}</div>
        </div>
      </div>

      <div class="mb-6 bg-white p-4 shadow rounded">
        <BarChart v-if="chartData" :data="chartData" title="Aperturas últimos 14 días" />
      </div>

      <div class="mb-6 bg-white p-4 shadow rounded">
        <PieChart v-if="deviceChartData" :data="deviceChartData" title="Ingresos por dispositivo" />
      </div>

      <div class="bg-white p-4 shadow rounded">
        <h3 class="font-semibold mb-2">Aperturas recientes</h3>
        <table class="w-full table-auto text-sm">
          <thead>
            <tr class="text-left">
              <th class="p-2">Email</th>
              <th class="p-2">IP</th>
              <th class="p-2">Referer</th>
              <th class="p-2">User agent</th>
              <th class="p-2">Fecha</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in opens" :key="row.id" class="border-t">
              <td class="p-2">{{ row.recipient_email || '-' }}</td>
              <td class="p-2">{{ row.ip_address || '-' }}</td>
              <td class="p-2 truncate max-w-xs">{{ row.referer || '-' }}</td>
              <td class="p-2 truncate max-w-xs">{{ row.user_agent || '-' }}</td>
              <td class="p-2">{{ formatDate(row.opened_at) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="mt-4 flex justify-between items-center">
          <div>Page {{ pagination.current_page }} / {{ pagination.total_pages }}</div>
          <div>
            <button class="px-3 py-1 mr-2 bg-gray-100 rounded" @click="prevPage" :disabled="pagination.current_page<=1">Anterior</button>
            <button class="px-3 py-1 bg-gray-100 rounded" @click="nextPage" :disabled="pagination.current_page>=pagination.total_pages">Siguiente</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import BarChart from '../components/BarChart.vue'
import PieChart from '../components/PieChart.vue'

const campaigns = ref([])
const selectedCampaign = ref('')
const loading = ref(false)
const kpis = ref({ total_opens: 0, unique_emails: 0, unique_ips: 0, days: [], counts: [] })
const chartData = ref(null)
const deviceChartData = ref(null)
const opens = ref([])
const pagination = ref({ current_page: 1, total_pages: 1 })

import Swal from 'sweetalert2'

const loadCampaigns = async () => {
  try {
    const res = await api.get('/api/staff/tracking/campaigns/')
    campaigns.value = res.data
    if (campaigns.value.length) {
      selectedCampaign.value = campaigns.value[0].campaign
      await loadCampaign()
    }
  } catch (e) {
    console.error(e)
    Swal.fire({ icon: 'error', title: 'Error', text: 'Error cargando campañas' })
  }
}

const loadCampaign = async (page = 1) => {
  if (!selectedCampaign.value) return
  loading.value = true
  try {
    const res = await api.get('/api/staff/tracking/kpis/', { params: { campaign: selectedCampaign.value } })
    kpis.value = res.data
    // Mostrar el contenido real (no el Proxy reactivo)
    console.log('tracking_kpis response (plain):', JSON.parse(JSON.stringify(kpis.value)))

    // Convertir a arrays planos para evitar proxies de Vue en Chart.js
    const labels = Array.isArray(kpis.value.days) ? [...kpis.value.days] : []
    const counts = Array.isArray(kpis.value.counts) ? kpis.value.counts.map(Number) : []

    chartData.value = {
      labels,
      datasets: [{ label: 'Aperturas', data: counts, backgroundColor: '#ef4444' }]
    }

    const deviceCounts = kpis.value.device_counts || {}
    deviceChartData.value = {
      labels: ['Celular', 'Escritorio', 'Otro'],
      datasets: [{
        label: 'Ingresos',
        data: [
          Number(deviceCounts.mobile || 0),
          Number(deviceCounts.desktop || 0),
          Number(deviceCounts.unknown || 0),
        ],
        backgroundColor: ['#ef4444', '#3b82f6', '#6b7280']
      }]
    }
    console.log('chartData prepared (plain):', JSON.parse(JSON.stringify(chartData.value)))
    console.log('deviceChartData prepared (plain):', JSON.parse(JSON.stringify(deviceChartData.value)))

    // load opens
    const res2 = await api.get('/api/staff/tracking/opens/', { params: { campaign: selectedCampaign.value, page } })
    opens.value = res2.data.results
    pagination.value = res2.data.pagination
  } catch (e) {
    console.error(e)
    Swal.fire({ icon: 'error', title: 'Error', text: 'Error cargando datos de tracking' })
  } finally {
    loading.value = false
  }
}

const onCampaignChange = () => {
  loadCampaign(1)
}

const prevPage = () => {
  if (pagination.value.current_page > 1) {
    loadCampaign(pagination.value.current_page - 1)
  }
}
const nextPage = () => {
  if (pagination.value.current_page < pagination.value.total_pages) {
    loadCampaign(pagination.value.current_page + 1)
  }
}

const formatDate = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString()
}

onMounted(() => {
  loadCampaigns()
})
</script>

<style scoped>
.truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
