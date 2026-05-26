
<template>
<!-- Navbar superior -->
      <nav class="bg-white/80 backdrop-blur-md border-b border-gray-300 sticky top-0 z-10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex justify-between h-16 items-center">
            <!-- Botón para abrir sidebar en móvil -->
            <button
              @click="toggleSidebar"
              class="md:hidden p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition"
            >
              <i class="fa fa-bars h-6 w-6"></i>
            </button>

            <!-- Título -->
            <div class="flex-1 flex items-center justify-center md:justify-start">
              <h1 class="text-lg font-semibold text-red-700 tracking-wide">FASA</h1>
            </div>

            <!-- Usuario y logout -->
            <div class="flex items-center space-x-3">
                <!-- Botón de instalación PWA (solo en móvil) -->
                <button
                  v-if="isInstallable && !isInstalled"
                  @click="installApp"
                  class="md:hidden text-blue-500 hover:text-blue-600 p-2 rounded-full transition-colors relative"
                  title="Instalar aplicación"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <!-- Pequeño indicador de nueva función (sin animación intrusiva) -->
                  <span class="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full h-3 w-3"></span>
                </button>

                <router-link to="/carrito" class="text-gray-500 hover:text-red-600 p-2 rounded-full relative">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    <span v-if="cart.totalItems > 0" class="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">{{ cart.totalItems }}</span>
                </router-link>

              <div class="flex items-center space-x-2 text-sm text-gray-600">
                <div class="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center text-white font-medium">
                  {{ initials }}
                </div>
                <span class="hidden sm:inline font-medium text-gray-600">{{ authStore.user?.username }}</span>
              </div>
              <button
                @click="authStore.logout"
                class="text-gray-500 hover:text-red-600 hover:bg-red-100 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-1"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>

                <span>Salir</span>
              </button>
            </div>
          </div>
        </div>
      </nav>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import Swal from 'sweetalert2'
import { useAuthStore } from '@/stores/auth'
import { cart } from '@/services/cart';

const emit = defineEmits(['toggleSidebar'])

const toggleSidebar = () => {
  emit('toggleSidebar')
}

const authStore = useAuthStore()

// PWA Installation Logic
const isInstallable = ref(false)
const isInstalled = ref(false)
let deferredPrompt = null

// Verificar si la app ya está instalada
const checkIfInstalled = () => {
  if (window.matchMedia('(display-mode: standalone)').matches) {
    isInstalled.value = true
    isInstallable.value = false
  }
}

onMounted(() => {
  checkIfInstalled()

  // Evento cuando el navegador puede mostrar el prompt de instalación
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferredPrompt = e
    isInstallable.value = true
  })

  // Evento cuando la app es instalada
  window.addEventListener('appinstalled', () => {
    isInstalled.value = true
    isInstallable.value = false
    console.log('App instalada correctamente')
  })
})

const installApp = async () => {
  if (!deferredPrompt) {
    Swal.fire({ icon: 'info', title: 'Instalación', text: 'Tu navegador no soporta la instalación de PWAs', confirmButtonColor: '#059669' })
    return
  }

  try {
    // Mostrar el prompt de instalación
    deferredPrompt.prompt()
    
    // Esperar a que el usuario responda
    const { outcome } = await deferredPrompt.userChoice
    
    if (outcome === 'accepted') {
      console.log('Usuario aceptó la instalación desde navbar')
    } else {
      console.log('Usuario rechazó la instalación')
    }
    
    // Limpiar el prompt
    deferredPrompt = null
    isInstallable.value = false
    
  } catch (error) {
    console.error('Error durante la instalación:', error)
    Swal.fire({ icon: 'error', title: 'Error', text: 'Error al instalar la aplicación: ' + (error?.message || ''), confirmButtonColor: '#dc2626' })
  }
}

// Iniciales del usuario
const initials = computed(() => {
  const user = authStore.user
  if (!user) return '?'
  return (user.first_name?.[0] || '') + (user.last_name?.[0] || '') || user.username?.[0]?.toUpperCase() || '?'
})
</script>