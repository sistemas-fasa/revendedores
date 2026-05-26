<template>
  <div class="container mx-auto p-6 bg-gray-50 min-h-screen">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Mis Pedidos</h1>
      <button 
        @click="cargarPedidos" 
        :disabled="loading"
        class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition disabled:opacity-50"
      >
        <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {{ loading ? 'Cargando...' : 'Actualizar' }}
      </button>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-lg shadow-md p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Filtrar por Estado:</label>
          <select 
            v-model="filtroEstado" 
            @change="aplicarFiltros"
            class="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-red-500"
          >
            <option value="">Todos los estados</option>
            <option value="PENDIENTE">Pendiente</option>
            <option value="CONFIRMADO">Confirmado</option>
            <option value="EN_PROCESO">En Proceso</option>
            <option value="PREPARADO">Preparado</option>
            <option value="ENVIADO">Enviado</option>
            <option value="ENTREGADO">Entregado</option>
            <option value="CANCELADO">Cancelado</option>
          </select>
        </div>
        
        <div class="flex-1"></div>
        
        <!-- Resumen rápido -->
        <div v-if="resumen" class="flex gap-4 text-sm">
          <span class="text-gray-600">Total: <strong>{{ resumen.total_pedidos }}</strong></span>
          <span class="text-yellow-600">Pendientes: <strong>{{ resumen.pedidos_pendientes }}</strong></span>
          <span class="text-green-600">Confirmados: <strong>{{ resumen.pedidos_confirmados }}</strong></span>
        </div>
      </div>
    </div>

    <!-- Estado de carga -->
    <div v-if="loading && pedidos.length === 0" class="flex justify-center items-center py-12">
      <div class="text-center">
        <svg class="animate-spin mx-auto h-12 w-12 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="mt-2 text-gray-600">Cargando pedidos...</p>
      </div>
    </div>

    <!-- Sin pedidos -->
    <div v-else-if="!loading && pedidos.length === 0" class="text-center py-12 bg-white rounded-lg shadow-md">
      <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No tienes pedidos aún</h3>
      <p class="text-gray-600 mb-4">¡Comienza a explorar nuestros productos y realiza tu primer pedido!</p>
      <router-link 
        to="/productos" 
        class="inline-block bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition"
      >
        Ver Productos
      </router-link>
    </div>

    <!-- Lista de pedidos -->
    <div v-else class="space-y-4">
      <div v-for="pedido in pedidos" :key="pedido.id" class="bg-white rounded-lg shadow-md p-6">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4">
          <div class="flex items-center space-x-4 mb-2 lg:mb-0">
            <h3 class="text-lg font-semibold text-gray-900">Pedido #{{ pedido.id }}</h3>
            <span :class="getEstadoClasses(pedido.estado)">
              {{ getEstadoTexto(pedido.estado) }}
            </span>
          </div>
          <div class="text-sm text-gray-600">
            <p>{{ formatDate(pedido.fecha_creacion) }}</p>
            <p class="font-semibold text-lg text-gray-900">${{ formatCurrency(pedido.total) }}</p>
          </div>
        </div>

        <!-- Items del pedido -->
        <div class="border-t pt-4">
          <h4 class="text-sm font-medium text-gray-700 mb-2">
            Productos ({{ pedido.items.length }} artículos)
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div v-for="item in pedido.items" :key="item.id" class="flex items-center space-x-3 p-2 bg-gray-50 rounded-md">
              <div class="flex-shrink-0">
                <img 
                  :src="getArticuloImagen(item)" 
                  :alt="getArticuloNombre(item)"
                  class="w-10 h-10 object-contain rounded"
                >
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ getArticuloNombre(item) }}</p>
                <p class="text-xs text-gray-500">{{ item.cantidad }} × ${{ formatCurrency(item.precio_unitario) }}</p>
              </div>
              <div class="text-sm font-medium text-gray-900">
                ${{ formatCurrency(item.subtotal) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Acciones -->
        <div class="flex justify-end space-x-2 mt-4 pt-4 border-t">
          <button 
            @click="verDetalle(pedido)"
            class="px-4 py-2 text-sm text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition"
          >
            Ver Detalle
          </button>
          <button 
            v-if="pedido.estado === 'PENDIENTE'"
            @click="cancelarPedido(pedido.id)"
            class="px-4 py-2 text-sm text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition"
          >
            Cancelar
          </button>
          <button 
            v-if="['CONFIRMADO', 'EN_PROCESO'].includes(pedido.estado)"
            @click="reordenar(pedido)"
            class="px-4 py-2 text-sm text-white bg-red-600 rounded-md hover:bg-red-700 transition"
          >
            Volver a Pedir
          </button>
        </div>
      </div>
    </div>

    <!-- Notificaciones -->
    <div v-if="notification.message" :class="notificationClasses" class="fixed top-4 right-4 max-w-sm w-full px-5 py-3 rounded-lg shadow-lg text-white text-sm flex items-center justify-between gap-2 z-50">
      <span>{{ notification.message }}</span>
      <button @click="notification = { message: '', type: '' }" class="text-white hover:text-gray-200 flex-shrink-0">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>

    <!-- Modal de Detalle del Pedido -->
    <div v-if="modalDetalle.show" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="cerrarModal">
      <div class="relative top-20 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white" @click.stop>
        <!-- Header del Modal -->
        <div class="flex items-center justify-between pb-3 border-b">
          <h3 class="text-lg font-semibold text-gray-900">
            Detalle del Pedido #{{ modalDetalle.pedido?.id }}
          </h3>
          <button @click="cerrarModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <!-- Contenido del Modal -->
        <div v-if="modalDetalle.pedido" class="mt-4">
          <!-- Información General -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div class="bg-gray-50 p-4 rounded-lg">
              <h4 class="font-semibold text-gray-900 mb-3">Información del Pedido</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-600">ID:</span>
                  <span class="font-medium">#{{ modalDetalle.pedido.id }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Estado:</span>
                  <span :class="getEstadoClasses(modalDetalle.pedido.estado)">
                    {{ getEstadoTexto(modalDetalle.pedido.estado) }}
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Fecha:</span>
                  <span class="font-medium">{{ formatDate(modalDetalle.pedido.fecha_creacion) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Total:</span>
                  <span class="font-bold text-lg text-green-600">${{ formatCurrency(modalDetalle.pedido.total) }}</span>
                </div>
              </div>
            </div>

            <div class="bg-blue-50 p-4 rounded-lg">
              <h4 class="font-semibold text-gray-900 mb-3">Resumen</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-600">Artículos:</span>
                  <span class="font-medium">{{ modalDetalle.pedido.items?.length || 0 }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Cantidad Total:</span>
                  <span class="font-medium">{{ getTotalCantidad(modalDetalle.pedido.items) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Usuario:</span>
                  <span class="font-medium">{{ modalDetalle.pedido.usuario_nombre || modalDetalle.pedido.user }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Lista Detallada de Productos -->
          <div class="mb-6">
            <h4 class="font-semibold text-gray-900 mb-3">Productos del Pedido</h4>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Producto</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precio Unit.</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subtotal</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="item in modalDetalle.pedido.items" :key="item.id">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div class="flex-shrink-0 h-12 w-12">
                          <img 
                            class="h-12 w-12 object-contain rounded-md" 
                            :src="getArticuloImagen(item)" 
                            :alt="getArticuloNombre(item)"
                          >
                        </div>
                        <div class="ml-4">
                          <div class="text-sm font-medium text-gray-900">{{ getArticuloNombre(item) }}</div>
                          <div class="text-sm text-gray-500">
                            Clave: {{ item.articulo_detalle?.clave || item.articulo || 'N/A' }}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${{ formatCurrency(item.precio_unitario) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ item.cantidad }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${{ formatCurrency(item.subtotal) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Acciones del Modal -->
          <div class="flex justify-end space-x-3 pt-4 border-t">
            <button
              @click="cerrarModal"
              class="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition"
            >
              Cerrar
            </button>
            <button
              v-if="['CONFIRMADO', 'EN_PROCESO'].includes(modalDetalle.pedido.estado)"
              @click="reordenar(modalDetalle.pedido); cerrarModal()"
              class="px-4 py-2 text-sm text-white bg-red-600 rounded-md hover:bg-red-700 transition"
            >
              Reordenar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';
import { cart } from '../services/cart';

const router = useRouter();
const loading = ref(false);
const pedidos = ref([]);
const resumen = ref(null);
const filtroEstado = ref('');
const notification = ref({ message: '', type: '' });
const modalDetalle = ref({ show: false, pedido: null });

const notificationClasses = computed(() => ({
  'bg-green-600': notification.value.type === 'success',
  'bg-red-700': notification.value.type === 'error',
  'bg-blue-600': notification.value.type === 'info',
}));

const showNotification = (message, type) => {
  notification.value = { message, type };
  setTimeout(() => {
    notification.value = { message: '', type: '' };
  }, 4000);
};

const formatCurrency = (value) => {
  const number = parseFloat(value);
  if (isNaN(number)) return value;
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number);
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

const getEstadoClasses = (estado) => {
  const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
  
  switch (estado) {
    case 'PENDIENTE':
      return `${baseClasses} bg-yellow-100 text-yellow-800`;
    case 'CONFIRMADO':
      return `${baseClasses} bg-blue-100 text-blue-800`;
    case 'EN_PROCESO':
      return `${baseClasses} bg-purple-100 text-purple-800`;
    case 'PREPARADO':
      return `${baseClasses} bg-indigo-100 text-indigo-800`;
    case 'ENVIADO':
      return `${baseClasses} bg-orange-100 text-orange-800`;
    case 'ENTREGADO':
      return `${baseClasses} bg-green-100 text-green-800`;
    case 'CANCELADO':
      return `${baseClasses} bg-red-100 text-red-800`;
    default:
      return `${baseClasses} bg-gray-100 text-gray-800`;
  }
};

const getEstadoTexto = (estado) => {
  const estados = {
    'PENDIENTE': 'Pendiente',
    'CONFIRMADO': 'Confirmado',
    'EN_PROCESO': 'En Proceso',
    'PREPARADO': 'Preparado',
    'ENVIADO': 'Enviado',
    'ENTREGADO': 'Entregado',
    'CANCELADO': 'Cancelado'
  };
  return estados[estado] || estado;
};

const getArticuloNombre = (item) => {
  // Manejar tanto el formato nuevo (articulo_detalle) como el antiguo (articulo)
  return item.articulo_detalle?.nombre || item.articulo?.nombre || 'Producto sin nombre';
};

const getArticuloImagen = (item) => {
  // Manejar tanto el formato nuevo (articulo_detalle) como el antiguo (articulo)
  return item.articulo_detalle?.imagen || item.articulo?.imagen || '/placeholder.png';
};

const cargarPedidos = async () => {
  loading.value = true;
  try {
    console.log('🔄 Cargando pedidos...');
    
    // Cargar pedidos con filtro
    const params = {};
    if (filtroEstado.value) {
      params.estado = filtroEstado.value;
    }
    
    const response = await api.get('/api/pedidos/', { params });
    pedidos.value = response.data;
    console.log('✅ Pedidos cargados:', pedidos.value.length);
    
    // Cargar resumen
    const resumenResponse = await api.get('/api/pedidos/mis_pedidos_resumen/');
    resumen.value = resumenResponse.data;
    console.log('📊 Resumen cargado:', resumen.value);
    
  } catch (error) {
    console.error('❌ Error al cargar pedidos:', error);
    showNotification('Error al cargar los pedidos. Intenta nuevamente.', 'error');
  } finally {
    loading.value = false;
  }
};

const aplicarFiltros = () => {
  cargarPedidos();
};

const verDetalle = (pedido) => {
  modalDetalle.value = { show: true, pedido: pedido };
  console.log('Abriendo modal para pedido:', pedido);
};

const cerrarModal = () => {
  modalDetalle.value = { show: false, pedido: null };
};

const getTotalCantidad = (items) => {
  if (!items) return 0;
  return items.reduce((total, item) => total + item.cantidad, 0);
};

const cancelarPedido = async (pedidoId) => {
  if (!confirm('¿Estás seguro de que quieres cancelar este pedido?')) {
    return;
  }
  
  try {
    // Aquí implementarías el endpoint para cancelar
    showNotification('Función de cancelación en desarrollo', 'info');
  } catch (error) {
    console.error('Error al cancelar pedido:', error);
    showNotification('Error al cancelar el pedido', 'error');
  }
};

const reordenar = async (pedido) => {
  try {
    console.log('🛒 Agregando productos del pedido al carrito...');
    
    // Limpiar carrito actual
    cart.clear();
    
    // Agregar todos los items del pedido al carrito
    for (const item of pedido.items) {
      // Obtener la información del artículo según el formato disponible
      const articuloData = item.articulo_detalle || item.articulo;
      
      if (articuloData) {
        cart.add(articuloData, item.cantidad);
      }
    }
    
    showNotification(`${pedido.items.length} productos agregados al carrito`, 'success');
    
    // Navegar al carrito
    setTimeout(() => {
      router.push('/carrito');
    }, 1000);
    
  } catch (error) {
    console.error('Error al reordenar:', error);
    showNotification('Error al agregar productos al carrito', 'error');
  }
};

onMounted(() => {
  cargarPedidos();
});
</script>
