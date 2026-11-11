<template>
  <div class="container mx-auto p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-2 text-gray-900">Artículos ocultos</h1>
    <p class="text-gray-600 mb-6">No aparecen en el catálogo ni en el buscador de la web. Por prefijo se oculta la familia entera (ej: REM, COR0).</p>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- Agregar por artículo -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Ocultar artículo</h2>
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
              v-if="!esOculto(art.clave)"
              @click="ocultarExacta(art.clave)"
              class="text-sm bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700"
            >Ocultar</button>
            <span v-else class="text-xs font-semibold text-red-700 bg-red-100 px-2 py-1 rounded">Oculto</span>
          </li>
        </ul>
        <p v-if="!buscando && resultados.length === 0" class="text-sm text-gray-500">Sin resultados. Buscá un artículo para ocultarlo.</p>

        <h2 class="text-xl font-semibold mt-8 mb-4">Ocultar por prefijo</h2>
        <div class="flex gap-2 mb-2">
          <input
            v-model="prefijo"
            type="text"
            placeholder="Ej: REM, COR0 (mín. 3 letras)"
            class="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500 uppercase"
          />
          <button @click="ocultarPrefijo" class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700">Ocultar</button>
        </div>
        <p class="text-xs text-gray-500">Oculta todos los artículos cuya clave empiece con ese texto.</p>
      </div>

      <!-- Listado actual -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold mb-4">Ocultos actuales ({{ ocultos.length }})</h2>
        <div v-if="loading" class="text-gray-500 text-sm">Cargando...</div>
        <ul v-else class="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          <li v-for="o in ocultos" :key="o.id" class="py-3 flex justify-between items-center gap-3">
            <div>
              <p class="font-semibold text-gray-900">
                <span class="text-xs font-semibold px-2 py-0.5 rounded mr-2" :class="o.tipo === 'prefijo' ? 'bg-amber-100 text-amber-800' : 'bg-gray-200 text-gray-700'">{{ o.tipo }}</span>{{ o.patron }}
              </p>
              <p class="text-xs text-gray-500">{{ o.motivo || 'sin motivo' }} · {{ o.creado_por_username || '' }}</p>
            </div>
            <button
              @click="mostrar(o)"
              class="text-sm border border-green-200 bg-green-50 text-green-700 px-3 py-1.5 rounded-lg hover:bg-green-100"
            >Mostrar</button>
          </li>
        </ul>
        <p v-if="!loading && ocultos.length === 0" class="text-sm text-gray-500">Nada oculto.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Swal from 'sweetalert2';
import api from '../services/api';

const ocultos = ref([]);
const resultados = ref([]);
const searchQuery = ref('');
const prefijo = ref('');
const loading = ref(false);
const buscando = ref(false);

const fetchOcultos = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/ocultos/', { params: { page_size: 200 } });
    ocultos.value = res.data.results || res.data;
  } catch (e) {
    console.error('Error al cargar ocultos:', e);
  } finally {
    loading.value = false;
  }
};

const patronesExactos = () => ocultos.value.filter((o) => o.tipo === 'exacta').map((o) => o.patron);
const patronesPrefijo = () => ocultos.value.filter((o) => o.tipo === 'prefijo').map((o) => o.patron);

const esOculto = (clave) =>
  patronesExactos().includes(clave) || patronesPrefijo().some((p) => clave.startsWith(p));

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

const crear = async (payload, okText) => {
  try {
    await api.post('/api/ocultos/', payload);
    await fetchOcultos();
    Swal.fire({ icon: 'success', title: okText, timer: 1500, showConfirmButton: false });
  } catch (e) {
    console.error('Error al ocultar:', e);
    Swal.fire({ icon: 'error', title: 'No se pudo ocultar', text: e.response?.data ? JSON.stringify(e.response.data) : 'No se pudo ocultar.' });
  }
};

const ocultarExacta = (clave) => crear({ tipo: 'exacta', patron: clave }, `${clave} oculto.`);
const ocultarPrefijo = () => {
  const p = prefijo.value.trim();
  if (p.length < 3) {
    Swal.fire({ icon: 'warning', title: 'Prefijo muy corto', text: 'Usá al menos 3 caracteres.' });
    return;
  }
  crear({ tipo: 'prefijo', patron: p }, `Prefijo ${p.toUpperCase()} oculto.`);
  prefijo.value = '';
};

const mostrar = async (o) => {
  const result = await Swal.fire({
    icon: 'warning',
    title: 'Volver a mostrar',
    text: `¿Mostrar de nuevo ${o.tipo} ${o.patron}?`,
    showCancelButton: true,
    confirmButtonText: 'Sí, mostrar',
    cancelButtonText: 'Cancelar',
    confirmButtonColor: '#16a34a',
  });
  if (!result.isConfirmed) return;
  try {
    await api.delete(`/api/ocultos/${o.id}/`);
    await fetchOcultos();
    Swal.fire({ icon: 'success', title: 'Visible de nuevo', timer: 1500, showConfirmButton: false });
  } catch (e) {
    console.error('Error al mostrar:', e);
    Swal.fire({ icon: 'error', title: 'Error', text: 'No se pudo revertir.' });
  }
};

onMounted(fetchOcultos);
</script>
