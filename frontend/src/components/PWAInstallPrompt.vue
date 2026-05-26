<template>
  <div v-if="showPrompt" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end justify-center p-4">
    <div class="bg-white rounded-t-2xl w-full max-w-md transform transition-transform duration-300 ease-out">
      <!-- Header del prompt -->
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900">Ferretería Avenida</h3>
              <p class="text-sm text-gray-500">Instalar aplicación</p>
            </div>
          </div>
          <button @click="dismissPrompt" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Contenido del prompt -->
      <div class="p-6">
        <h2 class="text-xl font-bold text-gray-900 mb-2">
          {{ isAndroid ? '¡Instala nuestra app!' : '¡Agrégala a tu pantalla de inicio!' }}
        </h2>
        <p class="text-gray-600 mb-4">
          {{ promptMessage }}
        </p>
        
        <!-- Beneficios -->
        <div class="space-y-2 mb-6">
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            <span class="text-sm text-gray-700">Acceso rápido desde tu pantalla de inicio</span>
          </div>
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            <span class="text-sm text-gray-700">Funciona sin conexión</span>
          </div>
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            <span class="text-sm text-gray-700">Experiencia de aplicación nativa</span>
          </div>
        </div>

        <!-- Botones de acción -->
        <div class="space-y-3">
          <button 
            v-if="isAndroid && canInstall"
            @click="installApp" 
            class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Instalar aplicación
          </button>
          
          <div v-else-if="isIOS" class="space-y-3">
            <div class="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
              <div class="flex items-center space-x-2 mb-2">
                <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                </svg>
                <span class="font-medium">Instrucciones para iOS:</span>
              </div>
              <ol class="list-decimal list-inside space-y-1">
                <li>Toca el botón <strong>Compartir</strong> en Safari</li>
                <li>Selecciona <strong>"Agregar a la pantalla de inicio"</strong></li>
                <li>Confirma tocando <strong>"Agregar"</strong></li>
              </ol>
            </div>
            <button @click="dismissPermanently" class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium">
              Entendido
            </button>
          </div>
          
          <button @click="remindLater" class="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-200 transition-colors">
            Recordar más tarde
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Estado del prompt
const showPrompt = ref(false)
const canInstall = ref(false)
let deferredPrompt = null

// Detectar plataforma
const isAndroid = computed(() => /Android/i.test(navigator.userAgent))
const isIOS = computed(() => /iPad|iPhone|iPod/.test(navigator.userAgent))
const isMobile = computed(() => isAndroid.value || isIOS.value)

// Mensajes según plataforma
const promptMessage = computed(() => {
  if (isAndroid.value) {
    return 'Instala nuestra aplicación para acceder más rápido y disfrutar de todas las funciones, incluso sin conexión.'
  } else if (isIOS.value) {
    return 'Agrega nuestra app a tu pantalla de inicio para un acceso más rápido y una mejor experiencia.'
  } else {
    return 'Instala nuestra aplicación para una mejor experiencia de usuario.'
  }
})

// Verificar si ya está instalada o en modo app
const isAppInstalled = () => {
  // Verificar si está en modo standalone (ya instalada)
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return true
  }
  
  // Verificar si viene de una PWA instalada (iOS)
  if (window.navigator.standalone === true) {
    return true
  }
  
  // Verificar si es una app instalada (Android/Chrome)
  if (document.referrer.startsWith('android-app://')) {
    return true
  }
  
  // Verificar localStorage si se instaló previamente
  if (localStorage.getItem('pwa_install_accepted') === 'true') {
    return true
  }
  
  return false
}

// Verificar si ya se mostró el prompt o se rechazó
const shouldShowPrompt = () => {
  const lastDismissed = localStorage.getItem('pwa_install_dismissed')
  const permanentlyDismissed = localStorage.getItem('pwa_install_permanent_dismiss')
  
  // No mostrar si se rechazó permanentemente
  if (permanentlyDismissed === 'true') {
    return false
  }
  
  // No mostrar si se rechazó hace menos de 3 días
  if (lastDismissed) {
    const dismissedTime = new Date(lastDismissed)
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
    if (dismissedTime > threeDaysAgo) {
      return false
    }
  }
  
  return true
}

// Contadores de interacción
const userInteractions = ref(0)
const hasViewedProducts = ref(false)

// Mostrar prompt después de cierta interacción del usuario
const schedulePrompt = () => {
  // Solo en móvil, si no está instalada y si debe mostrar
  if (!isMobile.value || isAppInstalled() || !shouldShowPrompt()) {
    return
  }
  
  // Escuchar interacciones del usuario
  const trackInteraction = () => {
    userInteractions.value++
    
    // Detectar si ha navegado o interactuado lo suficiente
    if (userInteractions.value >= 3 || hasViewedProducts.value) {
      // Mostrar después de un pequeño delay
      setTimeout(() => {
        showPrompt.value = true
      }, 2000)
      
      // Remover listeners para no mostrar múltiples veces
      document.removeEventListener('click', trackInteraction)
      document.removeEventListener('scroll', trackInteraction)
      window.removeEventListener('hashchange', trackInteraction)
    }
  }
  
  // Detectar navegación a páginas específicas
  const checkRoute = () => {
    const path = window.location.hash || window.location.pathname
    if (path.includes('productos') || path.includes('carrito') || path.includes('favoritos')) {
      hasViewedProducts.value = true
    }
  }
  
  // Agregar listeners
  document.addEventListener('click', trackInteraction)
  document.addEventListener('scroll', trackInteraction, { passive: true })
  window.addEventListener('hashchange', trackInteraction)
  
  // Verificar ruta inicial
  checkRoute()
  
  // Fallback: mostrar después de 45 segundos si no hay interacción
  setTimeout(() => {
    if (!showPrompt.value && shouldShowPrompt()) {
      showPrompt.value = true
    }
  }, 45000)
}

// Instalar aplicación (Android/Chrome)
const installApp = async () => {
  if (!deferredPrompt) {
    // Fallback si no hay prompt disponible
    alert('Para instalar la aplicación, busca la opción "Agregar a pantalla de inicio" en el menú de tu navegador.')
    dismissPrompt()
    return
  }

  try {
    // Mostrar el prompt nativo
    deferredPrompt.prompt()
    
    // Esperar respuesta del usuario
    const { outcome } = await deferredPrompt.userChoice
    
    if (outcome === 'accepted') {
      console.log('Usuario aceptó la instalación')
      localStorage.setItem('pwa_install_accepted', 'true')
    } else {
      console.log('Usuario rechazó la instalación')
      remindLater()
    }
    
    deferredPrompt = null
    canInstall.value = false
    showPrompt.value = false
    
  } catch (error) {
    console.error('Error durante la instalación:', error)
    dismissPrompt()
  }
}

// Recordar más tarde
const remindLater = () => {
  localStorage.setItem('pwa_install_dismissed', new Date().toISOString())
  showPrompt.value = false
}

// No volver a mostrar
const dismissPermanently = () => {
  localStorage.setItem('pwa_install_permanent_dismiss', 'true')
  showPrompt.value = false
}

// Cerrar prompt
const dismissPrompt = () => {
  remindLater()
}

onMounted(() => {
  // Evento para capturar el prompt de instalación
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferredPrompt = e
    canInstall.value = true
    console.log('PWA install prompt disponible')
  })

  // Evento cuando se instala la app
  window.addEventListener('appinstalled', () => {
    console.log('PWA instalada exitosamente')
    localStorage.setItem('pwa_install_accepted', 'true')
    showPrompt.value = false
  })

  // Programar mostrar el prompt
  schedulePrompt()
})

onUnmounted(() => {
  // Limpiar event listeners si es necesario
})
</script>

<style scoped>
/* Animación de entrada */
.fixed {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Estilo para el overlay */
.bg-black.bg-opacity-50 {
  backdrop-filter: blur(2px);
}
</style>