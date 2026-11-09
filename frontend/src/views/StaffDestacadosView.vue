<template>
  <div class="container mx-auto p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-2 text-gray-900">Destacados de Avenida</h1>
    <p class="text-gray-600 mb-6">Estos artículos aparecen primero en la búsqueda, antes que los favoritos de cada cliente.</p>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Buscador para agregar -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Agregar destacado</h2>
        <div class="flex gap-2 mb-4">
          <input
            v-model="searchQuery"
            @keyup.enter="buscar"
            type="text"
            placeholder="Buscar por clave o nombre..."
            class="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <button @click="buscar" class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700">Buscar</button>
        </div>
        <div v-if="buscando" class="text-gray-500 text-sm">Buscando...</div>
        <ul v-else class="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          <li v-for="art in resultados" :key="art.clave" class="py-3 flex justify-between items-center gap-3">
            <div>
              <p class="font-semibold text-gray-900">{{ art.nombre }}</p>
              <p class="text-xs text-gray-500">{{ art.clave }}</p>
            </div>
            <button
              v-if="!esDestacado(art.clave)"
              @click="agregar(art.clave)"
              class="text-sm bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700"
            >Destacar</button>
            <span v-else class="text-xs font-semibold text-green-700 bg-green-100 px-2 py-1 rounded">Destacado</span>
          </li>
        </ul>
        <p v-if="!buscando && resultados.length === 0" class="text-sm text-gray-500">Sin resultados. Buscá un artículo para destacarlo.</p>
      </div>

      <!-- Listado actual -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Destacados actuales ({{ destacados.length }})</h2>
        <div v-if="loading" class="text-gray-500 text-sm">Cargando...</div>
        <ul v-else class="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          <li v-for="d in destacados" :key="d.articulo" class="py-3 flex justify-between items-center gap-3">
            <div>
              <p class="font-semibold text-gray-900">{{ d.nombre || d.articulo }}</p>
              <p class="text-xs text-gray-500">{{ d.clave || d.articulo }}</p>
            </div>
            <button
              @click="quitar(d.articulo)"
              class="text-sm border border-red-200 bg-red-50 text-red-700 px-3 py-1.5 rounded-lg hover:bg-red-100"
            >Quitar</button>
          </li>
        </ul>
        <p v-if="!loading && destacados.length === 0" class="text-sm text-gray-500">Todavía no hay destacados.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const destacados = ref([]);
const resultados = ref([]);
const searchQuery = ref('');
const loading = ref(false);
const buscando = ref(false);

const fetchDestacados = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/destacados/', { params: { page_size: 100 } });
    destacados.value = res.data.results || res.data;
  } catch (e) {
    console.error('Error al cargar destacados:', e);
  } finally {
    loading.value = false;
  }
};

const esDestacado = (clave) => destacados.value.some((d) => (d.articulo === clave) || (d.clave === clave));

const buscar = async () => {
  if (!searchQuery.value.trim()) return;
  buscando.value = true;
  try {
    const res = await api.get('/api/articulos/', { params: { search: searchQuery.value.trim(), page_size: 20 } });
    resultados.value = res.data.results || [];
  } catch (e) {
    console.error('Error al buscar artículos:', e);
  } finally {
    buscando.value = false;
  }
};

const agregar = async (clave) => {
  try {
    await api.post('/api/destacados/', { articulo: clave });
    await fetchDestacados();
  } catch (e) {
    console.error('Error al destacar:', e);
    alert(e.response?.data ? JSON.stringify(e.response.data) : 'No se pudo destacar el artículo.');
  }
};

const quitar = async (clave) => {
  if (!confirm(`¿Quitar ${clave} de destacados?`)) return;
  try {
    await api.delete(`/api/destacados/${encodeURIComponent(clave)}/`);
    await fetchDestacados();
  } catch (e) {
    console.error('Error al quitar destacado:', e);
  }
};

onMounted(fetchDestacados);
</script>
