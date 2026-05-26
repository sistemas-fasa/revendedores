<!-- UserProfile.vue -->
<template>
  <div class="flex min-h-screen bg-gray-50 overflow-hidden">

    <!-- Contenido principal -->
    <div :class="['flex-1 transition-all duration-300', isSidebarOpen ? 'md:ml-64' : '']">
      

      <!-- Contenido del perfil -->
      <main class="flex-1 min-h-0 overflow-y-auto p-6 bg-gray-50 main-content">

        <div class="w-full">
          <!-- Tarjeta de perfil -->
          <div class="bg-white backdrop-blur-sm rounded-2xl shadow-lg border border-gray-300 overflow-hidden transition-all hover:shadow-xl">
            <!-- Encabezado -->
            <div class="bg-red-600 px-6 py-8 text-white text-center">
              <div class="w-20 h-20 bg-red-500 rounded-full mx-auto mb-3 flex items-center justify-center text-2xl font-bold">
                {{ initials }}
              </div>
              <h2 class="text-2xl font-semibold">{{ fullName }}</h2>
              <p class="opacity-90">{{ authStore.user?.is_staff ? 'Administrador' : 'Usuario' }}</p>
            </div>

            <!-- Formulario -->
            <form @submit.prevent="updateProfile" class="p-6 space-y-6">
              <!-- Nombre y Apellido -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-600 mb-1">Nombre</label>
                  <input
                    v-model="form.first_name"
                    type="text"
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                    placeholder="Tu nombre"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-600 mb-1">Apellido</label>
                  <input
                    v-model="form.last_name"
                    type="text"
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                    placeholder="Tu apellido"
                  />
                </div>
              </div>

              <!-- Email -->
              <div>
                <label class="block text-sm font-medium text-gray-600 mb-1">Email</label>
                <input
                  v-model="form.email"
                  type="email"
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                  placeholder="tu@ejemplo.com"
                />
              </div>

              <!-- Contraseña -->
              <div class="pt-4 border-t border-gray-300">
                <h3 class="text-lg font-medium text-gray-900 mb-3">Cambiar contraseña</h3>
                <div class="space-y-3">
                  <div>
                    <label class="block text-sm font-medium text-gray-600 mb-1">Nueva contraseña</label>
                    <input
                      v-model="form.password"
                      type="password"
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                      placeholder="••••••••"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-600 mb-1">Confirmar contraseña</label>
                    <input
                      v-model="form.password_confirmation"
                      type="password"
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
                <p class="text-xs text-gray-500 mt-1">Deja en blanco para no cambiar la contraseña.</p>
              </div>

              <!-- Mensaje de éxito/error -->
              <div v-if="message" class="p-3 text-sm rounded-lg bg-red-100 text-red-700 border border-red-300">
                {{ message }}
              </div>
              <div v-if="error" class="p-3 text-sm rounded-lg bg-red-50 text-red-700 border border-red-200">
                {{ error }}
              </div>

              <!-- Botón de guardar -->
              <div class="flex justify-end">
                <button
                  type="submit"
                  :disabled="loading"
                  class="bg-red-600 hover:bg-red-700 disabled:opacity-75 text-white px-6 py-2 rounded-lg font-medium transition flex items-center gap-2"
                >
                  <LoadingSpinner v-if="loading" class="h-4 w-4" />
                  <span>{{ loading ? 'Guardando...' : 'Guardar cambios' }}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { updateUserInfo } from '../api/user' // Vamos a crear esta función

// Íconos (puedes agregar más si usas un conjunto)
const LoadingSpinner = () => h('svg', {
  class: 'animate-spin h-4 w-4',
  fill: 'none',
  viewBox: '0 0 24 24'
}, [
  h('circle', {
    cx: '12',
    cy: '12',
    r: '10',
    stroke: 'currentColor',
    'stroke-width': '4',
    class: 'opacity-25'
  }),
  h('path', {
    fill: 'currentColor',
    d: 'M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z',
    class: 'opacity-75'
  })
])

const authStore = useAuthStore()

// Datos del formulario
const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  password_confirmation: ''
})

const message = ref('')
const error = ref('')
const loading = ref(false)

// Iniciales del usuario
const initials = computed(() => {
  const user = authStore.user
  return (user?.first_name?.[0] || '') + (user?.last_name?.[0] || '') || user?.username?.[0]?.toUpperCase() || '?'
})

// Nombre completo
const fullName = computed(() => {
  const { first_name, last_name } = form.value
  if (first_name && last_name) return `${first_name} ${last_name}`
  return first_name || last_name || 'Sin nombre'
})

// Cargar datos del usuario al montar
onMounted(() => {
  const user = authStore.user
  if (user) {
    form.value.first_name = user.first_name || ''
    form.value.last_name = user.last_name || ''
    form.value.email = user.email || ''
  }
})

// Guardar cambios
const updateProfile = async () => {
  message.value = ''
  error.value = ''
  loading.value = true

  // Validación de contraseñas
  if (form.value.password && form.value.password !== form.value.password_confirmation) {
    error.value = 'Las contraseñas no coinciden.'
    loading.value = false
    return
  }

  try {
    const userData = {
      first_name: form.value.first_name.trim(),
      last_name: form.value.last_name.trim(),
      email: form.value.email.trim()
    }

    // Solo incluir password si se ha ingresado
    if (form.value.password) {
      userData.password = form.value.password
    }

    await updateUserInfo(userData) // Llamada a la API

    // Actualizar el store
    authStore.user = { ...authStore.user, ...userData }
    delete userData.password // No guardar en el store

    message.value = 'Perfil actualizado con éxito.'
    // Limpiar contraseña
    form.value.password = ''
    form.value.password_confirmation = ''
  } catch (err) {
    error.value = err.message || 'Error al actualizar el perfil.'
  } finally {
    loading.value = false
  }
}
</script>