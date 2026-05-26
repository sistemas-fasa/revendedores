<template>
  <div class="container mx-auto p-6 bg-gray-50 min-h-screen">
    <div class="max-w-2xl mx-auto">
      <!-- Header de confirmación -->
      <div class="bg-white rounded-lg shadow-md p-8 text-center mb-6">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">¡Pedido Confirmado!</h1>
        <p class="text-lg text-gray-600">Tu pedido ha sido procesado exitosamente</p>
      </div>

      <!-- Información del pedido -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Detalles del Pedido</h2>
        
        <div class="border-b border-gray-200 pb-4 mb-4">
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Número de Pedido:</span>
            <span class="font-semibold text-gray-900">#{{ pedidoId }}</span>
          </div>
          <div class="flex justify-between items-center mt-2">
            <span class="text-gray-600">Estado:</span>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              CONFIRMADO
            </span>
          </div>
          <div class="flex justify-between items-center mt-2">
            <span class="text-gray-600">Fecha:</span>
            <span class="text-gray-900">{{ formatDate(new Date()) }}</span>
          </div>
        </div>

        <!-- Mensaje sobre el correo -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <svg class="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-blue-800 mb-1">Confirmación por Correo</h3>
              <p class="text-sm text-blue-700">
                Estamos enviando un correo de confirmación con todos los detalles de tu pedido. 
                <strong>Por favor, verifica tu casilla de entrada</strong> y también la carpeta de spam o correo no deseado.
              </p>
              <div v-if="emailStatus === 'sending'" class="mt-2 flex items-center text-xs text-blue-600">
                <svg class="animate-spin -ml-1 mr-2 h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Enviando correo de confirmación...
              </div>
              <div v-else-if="emailStatus === 'sent'" class="mt-2 flex items-center text-xs text-green-700">
                <svg class="-ml-0.5 mr-2 h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Correo de confirmación enviado.
              </div>
              <div v-else-if="emailStatus === 'failed'" class="mt-2 flex items-center text-xs text-yellow-700">
                <svg class="-ml-0.5 mr-2 h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
                No pudimos confirmar el envío del correo.
              </div>
            </div>
          </div>
        </div>

        <!-- Mensaje de advertencia si el correo falló (opcional) -->
        <div v-if="warning" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <svg class="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-yellow-800">Atención</h3>
              <p class="text-sm text-yellow-700">{{ warning }}</p>
            </div>
          </div>
        </div>

        <!-- Información adicional -->
        <div class="bg-gray-50 rounded-lg p-4">
          <h3 class="text-sm font-medium text-gray-900 mb-2">¿Qué sigue?</h3>
          <ul class="text-sm text-gray-600 space-y-1">
            <li>• Recibirás un correo con la confirmación y detalles del pedido</li>
            <li>• Nuestro equipo procesará tu pedido</li>
            <li>• Te contactaremos para coordinar la entrega</li>
            <li>• Si tienes dudas, puedes contactarnos</li>
          </ul>
        </div>
      </div>

      <!-- Botones de acción -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex flex-col sm:flex-row gap-4">
          <router-link 
            to="/pedidos" 
            class="flex-1 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition text-center font-medium"
          >
            Ver Mis Pedidos
          </router-link>
          <router-link 
            to="/productos" 
            class="flex-1 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-200 transition text-center font-medium"
          >
            Seguir Comprando
          </router-link>
        </div>
        
        <div class="mt-4 text-center">
          <p class="text-sm text-gray-500">
            ¿Necesitas ayuda? 
            <a href="mailto:ventas@tuempresa.com" class="text-red-600 hover:text-red-700 underline">
              Contáctanos
            </a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const pedidoId = ref(null);
const warning = ref('');
const emailStatus = ref('sending');

onMounted(() => {
  // Obtener el ID del pedido desde los parámetros de la ruta o query
  pedidoId.value = route.params.id || route.query.pedido || 'N/A';
  
  // Verificar si hay advertencias sobre el correo
  if (route.query.correoError) {
    warning.value = 'El pedido se procesó correctamente, pero no pudimos enviarte un correo de confirmación. Por favor contáctanos si tienes dudas sobre tu pedido.';
    emailStatus.value = 'failed';
  } else {
    emailStatus.value = 'sending';
    setTimeout(() => {
      emailStatus.value = 'sent';
    }, 3500);
  }
});

const formatDate = (date) => {
  return new Intl.DateTimeFormat('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};
</script>