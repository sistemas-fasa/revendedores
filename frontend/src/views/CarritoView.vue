<template>
  <div class="container mx-auto p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-6 text-gray-900">Carrito de Compras</h1>

    <div v-if="cart.items.length === 0" class="text-center py-10 bg-white rounded-lg shadow-md">
      <p class="text-xl text-gray-600 mb-4">Tu carrito está vacío.</p>
      <router-link to="/articulos" class="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition">
        Volver a la tienda
      </router-link>
    </div>

    <div v-else>
      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Artículo</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unidad</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precio</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Peso (kg)</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subtotal</th>
              <th scope="col" class="relative px-6 py-3">
                <span class="sr-only">Eliminar</span>
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="item in cart.items" :key="item.articulo.clave">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-16 w-16">
                    <img class="h-16 w-16 object-contain rounded-md" :src="item.articulo.imagen || '/placeholder.png'" :alt="item.articulo.nombre">
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">{{ item.articulo.nombre }}</div>
                    <div class="text-sm text-gray-500">Clave: {{ item.articulo.clave }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-700 font-medium">{{ item.articulo.unidad || 'UN' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">$ {{ formatCurrency(item.precio_unitario) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <input 
                    type="number" 
                    :min="getMinQuantity(item)" 
                    :step="getStepQuantity(item)"
                    v-model.number="item.cantidad" 
                    @change="handleQuantityChange(item)" 
                    class="w-20 px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-red-500"
                  >
                  <span v-if="item.articulo.campoa1?.toLowerCase() === 'a' && item.articulo.mts2 > 0" class="text-xs text-gray-500">
                    ({{ (item.cantidad / item.articulo.mts2).toFixed(0) }} cajas)
                  </span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-700">
                  {{ formatWeight(item) }}
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-bold text-gray-900">$ {{ formatCurrency(item.subtotal) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button @click="cart.remove(item.articulo.clave)" class="text-red-600 hover:text-red-900">
                  Eliminar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mt-6 bg-white rounded-lg shadow-md p-6 flex justify-end items-center">
        <div class="text-right">
          <p class="text-2xl font-bold text-gray-900">Total: $ {{ formatCurrency(cart.totalPrice) }}</p>
          <p class="text-sm text-gray-500">({{ cart.totalItems }} artículos)</p>
          <p class="text-lg font-semibold text-gray-700 mt-2">Peso Total: {{ formatWeightDisplay(totalWeight) }} kg</p>
          <p class="mt-3 text-xs text-gray-500 max-w-md">
            El precio total es orientativo. El sector de ventas se contactará para confirmar los precios reales
            con bonificaciones y descuentos por compras en cantidad.
          </p>
          <button @click="checkout" :disabled="loading || cart.items.length === 0" class="mt-4 w-full bg-red-600 text-white px-8 py-3 rounded-lg hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center">
            <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span v-if="loading">{{ processingStep || 'Procesando pedido...' }}</span>
            <span v-else>Confirmar Pedido</span>
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { cart } from '@/services/cart';

const router = useRouter();
const loading = ref(false);
const processingStep = ref('');
const notification = ref({ message: '', type: '' });

const formatCurrency = (value) => {
  const number = parseFloat(value);
  if (isNaN(number)) return value;
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number);
};

// Formatear peso con máximo 3 decimales
const formatWeightDisplay = (value) => {
  const number = parseFloat(value);
  if (isNaN(number)) return '0.000';
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(number);
};

// Formatear el peso de un item
const formatWeight = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase();
  const pesoUnitario = parseFloat(item.articulo.peso) || 0;
  
  // Si es tipo A con mts2, el peso es: (cantidad en m² / mts2 por caja) × peso por caja
  if (campoa1Lower === 'a' && item.articulo.mts2 > 0) {
    const cajas = item.cantidad / item.articulo.mts2;
    const pesoTotal = cajas * pesoUnitario;
    return pesoTotal.toFixed(3);
  }
  
  // Si es tipo C, el peso ya viene calculado o es: cantidad × peso unitario
  if (campoa1Lower === 'c') {
    const pesoTotal = item.cantidad * pesoUnitario;
    return pesoTotal.toFixed(3);
  }
  
  // Para otros tipos: cantidad × peso unitario
  const pesoTotal = item.cantidad * pesoUnitario;
  return pesoTotal.toFixed(3);
};

// Calcular el peso total del pedido
const totalWeight = computed(() => {
  return cart.items.reduce((total, item) => {
    const peso = parseFloat(formatWeight(item)) || 0;
    return total + peso;
  }, 0);
});

// Obtener el mínimo de cantidad según el tipo de artículo
const getMinQuantity = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase();
  
  // Para tipo A con mts2, el mínimo es un múltiplo de mts2
  if (campoa1Lower === 'a' && item.articulo.mts2 > 0) {
    return item.articulo.mts2;
  }
  
  return 1;
};

// Obtener el step de cantidad según el tipo de artículo
const getStepQuantity = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase();
  
  // Para tipo A con mts2, el step es el mts2 (múltiplos exactos)
  if (campoa1Lower === 'a' && item.articulo.mts2 > 0) {
    return item.articulo.mts2;
  }
  
  return 1;
};

// Manejar cambio de cantidad con validación de múltiplos
const handleQuantityChange = (item) => {
  const campoa1Lower = (item.articulo.campoa1 || '').toLowerCase();
  
  // Si es tipo A con mts2, ajustar a múltiplo exacto
  if (campoa1Lower === 'a' && item.articulo.mts2 > 0 && item.cantidad > 0) {
    const mts2 = parseFloat(item.articulo.mts2);
    
    // Calcular cuántas cajas corresponden a los m² ingresados
    const cajas = Math.ceil(item.cantidad / mts2);
    
    // Ajustar la cantidad a múltiplo exacto (cajas × mts2)
    const cantidadAjustada = cajas * mts2;
    
    if (Math.abs(item.cantidad - cantidadAjustada) > 0.01) {
      console.log(`🔧 Ajustando cantidad de ${item.cantidad} m² a ${cantidadAjustada} m² (${cajas} cajas × ${mts2} m²/caja)`);
      item.cantidad = cantidadAjustada;
      
      showNotification(`Cantidad ajustada a ${cantidadAjustada.toFixed(2)} m² (${cajas} caja${cajas > 1 ? 's' : ''})`, 'info');
    }
  }
  
  // Actualizar el carrito
  cart.updateQuantity(item.articulo.clave, item.cantidad);
};

const notificationClasses = computed(() => ({
    'bg-green-600': notification.value.type === 'success',
    'bg-red-700': notification.value.type === 'error',
    'bg-blue-600': notification.value.type === 'info',
}));

const showNotification = (message, type) => {
    notification.value = { message, type };
    const duration = type === 'error' ? 5000 : 3000; // Errores se muestran más tiempo
    setTimeout(() => {
        notification.value = { message: '', type: '' };
    }, duration);
};

const checkout = async () => {
    if (cart.items.length === 0) {
        showNotification('El carrito está vacío', 'error');
        return;
    }

    console.log('🚀 Iniciando proceso de checkout desde CarritoView');
    loading.value = true;
    processingStep.value = 'Procesando pedido...';
    
    try {
        console.log('📞 Llamando a cart.checkout()...');
        
        const result = await cart.checkout((step) => {
            processingStep.value = step;
            console.log('📈 Progreso:', step);
        });
        
        console.log('📨 Resultado del checkout:', result);
        
        if (result.success) {
            processingStep.value = 'Pedido confirmado!';
            showNotification(result.message || 'Pedido realizado con éxito! Recibirás un correo de confirmación.', 'success');
            console.log('✅ Redirigiendo a página de confirmación...');
            setTimeout(() => {
                // Redirigir a la página de confirmación con el ID del pedido
                const pedidoId = result.pedido?.id || 'N/A';
                router.push(`/pedido-confirmado/${pedidoId}`);
            }, 1500);
        } else {
            console.warn('⚠️ Checkout falló:', result.message);
            processingStep.value = 'Error en el proceso';
            showNotification(result.message || 'Error al procesar el pedido. Intente de nuevo.', 'error');
        }
    } catch (error) {
        console.error('💥 Excepción en checkout:', error);
        
        // Manejo de errores más específico
        let errorMessage = 'Error al procesar el pedido. Intente de nuevo.';
        
        if (error.response) {
            // Error del servidor
            if (error.response.status === 401) {
                errorMessage = 'Su sesión ha expirado. Inicie sesión nuevamente.';
            } else if (error.response.status === 400) {
                errorMessage = error.response.data?.error || 'Datos del pedido inválidos.';
            } else if (error.response.status >= 500) {
                errorMessage = 'Error interno del servidor. Intente más tarde.';
            }
        } else if (error.message && error.message.includes('Timeout')) {
            errorMessage = 'El proceso tardó más de lo esperado. Verifique su pedido en su cuenta.';
        } else if (error.code === 'NETWORK_ERROR') {
            errorMessage = 'Error de conexión. Verifique su conexión a internet.';
        }
        
        processingStep.value = 'Error en el proceso';
        showNotification(errorMessage, 'error');
    } finally {
        loading.value = false;
        processingStep.value = '';
    }
};
</script>