<template>
  <nav class="sticky top-0 z-20 border-b border-gray-200 bg-white">
    <div class="px-4 sm:px-6">
      <div class="flex h-16 items-center justify-between gap-3">
        <button
          @click="toggleSidebar"
          class="rounded-lg p-2 text-gray-600 transition hover:bg-gray-100 hover:text-gray-950 md:hidden"
          aria-label="Abrir menú"
        >
          <i class="fa fa-bars h-6 w-6"></i>
        </button>

        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-bold text-gray-950">Ferretería Avenida</p>
          <p class="hidden text-xs text-gray-500 sm:block">Portal de revendedores</p>
        </div>

        <div class="flex items-center gap-2 sm:gap-3">
          <button
            v-if="isInstallable && !isInstalled"
            @click="installApp"
            class="relative rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-red-700 md:hidden"
            title="Instalar aplicación"
            aria-label="Instalar aplicación"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span class="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-red-700"></span>
          </button>

          <router-link to="/carrito" class="relative rounded-lg border border-gray-200 bg-white p-2 text-gray-600 shadow-sm transition hover:border-red-200 hover:text-red-700" aria-label="Ver carrito">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <span v-if="cart.totalItems > 0" class="absolute -right-2 -top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-700 px-1 text-xs font-bold text-white">{{ cart.totalItems }}</span>
          </router-link>

          <div class="hidden items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-sm text-gray-600 sm:flex">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-red-700 text-sm font-bold text-white">
              {{ initials }}
            </div>
            <span class="max-w-32 truncate font-semibold text-gray-700">{{ authStore.user?.username }}</span>
          </div>

          <button
            @click="authStore.logout"
            class="ui-button ui-button-secondary px-3 py-2 text-sm"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span class="hidden sm:inline">Salir</span>
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import Swal from 'sweetalert2'
import { useAuthStore } from '@/stores/auth'
import { cart } from '@/services/cart'

const emit = defineEmits(['toggleSidebar'])

const toggleSidebar = () => {
  emit('toggleSidebar')
}

const authStore = useAuthStore()
const isInstallable = ref(false)
const isInstalled = ref(false)
let deferredPrompt = null

const checkIfInstalled = () => {
  if (window.matchMedia('(display-mode: standalone)').matches) {
    isInstalled.value = true
    isInstallable.value = false
  }
}

onMounted(() => {
  checkIfInstalled()

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferredPrompt = e
    isInstallable.value = true
  })

  window.addEventListener('appinstalled', () => {
    isInstalled.value = true
    isInstallable.value = false
  })
})

const installApp = async () => {
  if (!deferredPrompt) {
    Swal.fire({ icon: 'info', title: 'Instalación', text: 'Tu navegador no soporta la instalación de PWAs', confirmButtonColor: '#c81e1e' })
    return
  }

  try {
    deferredPrompt.prompt()
    await deferredPrompt.userChoice
    deferredPrompt = null
    isInstallable.value = false
  } catch (error) {
    Swal.fire({ icon: 'error', title: 'Error', text: 'Error al instalar la aplicación: ' + (error?.message || ''), confirmButtonColor: '#c81e1e' })
  }
}

const initials = computed(() => {
  const user = authStore.user
  if (!user) return '?'
  return (user.first_name?.[0] || '') + (user.last_name?.[0] || '') || user.username?.[0]?.toUpperCase() || '?'
})
</script>
