<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const show = ref(false)
const offersCount = ref(0)
const showOnDashboard = ref(false)
const lastShownLoginAt = ref(0)
const route = useRoute()
const loading = ref(false)

const triggerModalIfNeeded = () => {
  offersCount.value = authStore.offersCount || 0
  if (!authStore.isAuthenticated || offersCount.value <= 0) return

  // Mostrar una sola vez por login
  if (authStore.lastLoginAt && authStore.lastLoginAt === lastShownLoginAt.value) return

  if (route.path === '/dashboard') {
    show.value = true
    lastShownLoginAt.value = authStore.lastLoginAt
  } else {
    showOnDashboard.value = true
  }
}

// Cuando cambia a autenticado, comprobar ofertas
watch(() => authStore.isAuthenticated, (val) => {
  if (val) triggerModalIfNeeded()
})

// También intentar onMounted si ya autenticado
onMounted(() => {
  offersCount.value = authStore.offersCount || 0
  if (authStore.isAuthenticated) triggerModalIfNeeded()
  try { window.addEventListener('user-logged-in', triggerModalIfNeeded) } catch (e) {}
})

onUnmounted(() => {
  try { window.removeEventListener('user-logged-in', triggerModalIfNeeded) } catch (e) {}
})

// Si el usuario navega a /dashboard y había ofertas detectadas, mostrar el modal
watch(() => route.path, (p) => {
  if (p === '/dashboard' && offersCount.value > 0) {
    show.value = true
    lastShownLoginAt.value = authStore.lastLoginAt
    showOnDashboard.value = false
  }
})

const goToOffers = () => {
  show.value = false
  router.push({ path: '/productos', query: { oferta: '1' } })
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60" @click.self="show = false">
    <div class="bg-white rounded-lg shadow-2xl max-w-xl w-full p-6 mx-4">
      <div class="flex items-start justify-between">
        <h3 class="text-xl font-bold text-gray-900">Ofertas vigentes</h3>
        <button @click="show = false" class="text-gray-500 hover:text-gray-700">✕</button>
      </div>

      <p class="mt-3 text-gray-700">Hay {{ offersCount }} ofertas vigentes. Puedes ver el detalle en la sección de ofertas.</p>

      <div class="mt-5 flex gap-3">
        <button @click.prevent="goToOffers" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition">Ver Ofertas</button>
        <button @click.prevent="() => { show = false }" class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition">Cerrar</button>
      </div>

      <p class="mt-4 text-xs text-gray-500">No volver a mostrar esta notificación en esta sesión.</p>
    </div>
  </div>
</template>
