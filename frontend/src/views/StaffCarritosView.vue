<template>
  <div class="container mx-auto p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-6 text-gray-900">Carritos de Clientes</h1>

    <div v-if="loading" class="flex justify-center items-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
    </div>

    <div v-else-if="carritos.length === 0" class="text-center py-10 bg-white rounded-lg shadow-md">
      <p class="text-xl text-gray-600">No hay carritos activos en este momento.</p>
    </div>

    <div v-else class="space-y-6">
      <div v-for="carrito in carritos" :key="carrito.usuario" class="bg-white rounded-lg shadow-md overflow-hidden">
        <!-- Header del carrito -->
        <div class="bg-gradient-to-r from-red-600 to-red-700 text-white px-6 py-4">
          <div class="flex justify-between items-center">
            <div>
              <h2 class="text-xl font-bold">{{ carrito.usuario_nombre }}</h2>
              <p class="text-sm text-red-100">Cliente #{{ carrito.numero_cliente }}</p>
              <p v-if="carrito.ultima_modificacion || carrito.ultimo_acceso" class="text-xs text-red-100 mt-1">
                Última actividad:
                <span :class="isUpdated(carrito.usuario) ? 'bg-white/30 px-1 rounded transition-all duration-700' : ''">{{ timeAgo(carrito.ultima_modificacion || carrito.ultimo_acceso) }}</span>
                <span class="ml-2 text-[10px]">({{ formatDate(carrito.ultima_modificacion || carrito.ultimo_acceso) }})</span>
              </p>
            </div>
            <div class="text-right">
              <p class="text-2xl font-bold">${{ formatCurrency(carrito.total) }}</p>
              <p class="text-sm text-red-100">{{ carrito.items.length }} item(s)</p>
            </div>
          </div>
        </div>

        <!-- Items del carrito -->
        <div class="p-6">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Artículo</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unidad</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cantidad</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Peso (kg)</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subtotal</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="item in carrito.items" :key="item.articulo.clave" class="hover:bg-gray-50">
                <td class="px-4 py-3">
                  <div class="flex items-center">
                    <div class="flex-shrink-0 h-12 w-12">
                      <img class="h-12 w-12 object-contain rounded" :src="item.articulo.imagen || '/placeholder.png'" :alt="item.articulo.nombre">
                    </div>
                    <div class="ml-3">
                      <div class="text-sm font-medium text-gray-900">{{ item.articulo.nombre }}</div>
                      <div class="text-xs text-gray-500">{{ item.articulo.clave }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ item.articulo.unidad || 'UN' }}</td>
                <td class="px-4 py-3 text-sm text-gray-900">${{ formatCurrency(item.precio_unitario) }}</td>
                <td class="px-4 py-3 text-sm text-gray-900">{{ formatCurrency(item.cantidad) }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ formatWeight(item) }}</td>
                <td class="px-4 py-3 text-sm font-semibold text-gray-900">${{ formatCurrency(item.subtotal) }}</td>
              </tr>
            </tbody>
          </table>

          <!-- Total del carrito -->
          <div class="mt-4 pt-4 border-t border-gray-200 flex justify-end">
            <div class="text-right">
              <p class="text-lg font-semibold text-gray-700">Peso Total: {{ formatWeightDisplay(carrito.peso_total) }} kg</p>
              <p class="text-2xl font-bold text-gray-900 mt-1">Total: ${{ formatCurrency(carrito.total) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import api from '../services/api';

const loading = ref(true);
const carritos = ref([]);

const formatCurrency = (value) => {
  const number = parseFloat(value);
  if (isNaN(number)) return value;
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number);
};

const formatWeightDisplay = (value) => {
  const number = parseFloat(value);
  if (isNaN(number)) return '0.000';
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(number);
};

const formatDate = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return isoString;
  const pad = (n) => String(n).padStart(2, '0');
  const day = pad(d.getDate());
  const month = pad(d.getMonth() + 1);
  const year = d.getFullYear();
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  return `${day}-${month}-${year} ${hours}:${minutes}`;
};

const timeAgo = (isoString) => {
  // reference nowTick so Vue tracks reactivity and recomputes when it changes
  void nowTick.value;
  if (!isoString) return 'sin actividad';
  const now = new Date(nowTick.value);
  const then = new Date(isoString);
  if (isNaN(then.getTime())) return isoString;
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return `hace ${diffSec} seg${diffSec === 1 ? '' : 's'}`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `hace ${diffMin} min${diffMin === 1 ? '' : 's'}`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `hace ${diffHrs} hora${diffHrs === 1 ? '' : 's'}`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 30) return `hace ${diffDays} día${diffDays === 1 ? '' : 's'}`;
  // Fallback to formatted date for older entries
  return formatDate(isoString);
};

const formatWeight = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase();
  const pesoUnitario = parseFloat(item.articulo.peso) || 0;
  
  if (campoa1Lower === 'a' && item.articulo.mts2 > 0) {
    const cajas = item.cantidad / item.articulo.mts2;
    const pesoTotal = cajas * pesoUnitario;
    return pesoTotal.toFixed(3);
  }
  
  if (campoa1Lower === 'c') {
    const pesoTotal = item.cantidad * pesoUnitario;
    return pesoTotal.toFixed(3);
  }
  
  const pesoTotal = item.cantidad * pesoUnitario;
  return pesoTotal.toFixed(3);
};

const fetchCarritos = async () => {
  try {
    loading.value = true;
    const response = await api.get('/api/staff/carritos/');
    carritos.value = response.data;
    // detect changes and mark for highlight
    carritos.value.forEach((c) => markIfChanged(c));
    console.log('📦 Carritos cargados:', carritos.value);
  } catch (error) {
    console.error('❌ Error al cargar carritos:', error);
  } finally {
    loading.value = false;
  }
};

// reactive tick to force timeAgo updates every interval
const nowTick = ref(Date.now());
let tickInterval = null;
// map usuario -> previous label
const previousTimeLabels = ref({});
// flags to trigger a short highlight when the label changes
const updatedFlags = ref({});
// periodic fetch interval id
let fetchInterval = null;
// configurable refresh interval in ms (default 5 minutes)
const refreshIntervalMs = 5 * 60 * 1000;

onMounted(() => {
  fetchCarritos();
  // update tick every 30 seconds
  tickInterval = setInterval(() => {
    nowTick.value = Date.now();
      // check labels for changes due to passage of time
      (carritos.value || []).forEach((c) => markIfChanged(c));
  }, 30 * 1000);
    // also periodically refresh the carritos list from server
    fetchInterval = setInterval(() => {
      fetchCarritos();
    }, refreshIntervalMs);
});

onUnmounted(() => {
  if (tickInterval) clearInterval(tickInterval);
    if (fetchInterval) clearInterval(fetchInterval);
});

// mark updated flags when labels change
const markIfChanged = (carrito) => {
  try {
    const id = carrito.usuario;
    const label = timeAgo(carrito.ultima_modificacion || carrito.ultimo_acceso);
    if (previousTimeLabels.value[id] === undefined) {
      previousTimeLabels.value[id] = label;
      return;
    }
    if (previousTimeLabels.value[id] !== label) {
      updatedFlags.value[id] = true;
      previousTimeLabels.value[id] = label;
      // remove the highlight after 700ms
      setTimeout(() => {
        updatedFlags.value[id] = false;
      }, 700);
    }
  } catch (e) {
    // ignore
  }
};

const isUpdated = (id) => {
  return !!(updatedFlags.value && updatedFlags.value[id]);
};
</script>
