<template>
  <div class="min-h-screen flex flex-col md:flex-row bg-gray-50">
    <!-- Sección izquierda: Branding con logo -->
    <div class="w-full md:w-1/2 flex items-center justify-center p-8 lg:p-12 relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-red-600/10 to-red-800/20"></div>
      <div class="relative z-10 text-center max-w-lg mx-auto">
        <!-- Logo -->
        <div class="flex justify-center mb-6">
          <img src="/logo.png" alt="Ferretería Avenida S.A." class="h-20 sm:h-24 object-contain" />
        </div>

        <div class="bg-white/20 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/30">
          <h1 class="text-2xl sm:text-3xl font-extrabold text-black leading-tight">
            Bienvenido a
            <span class="text-red-600 font-bold">Ferretería Avenida</span>
          </h1>
          <p class="mt-4 text-base text-gray-700 leading-relaxed">
            Gestiona tus ventas desde cualquier lugar.
          </p>
          <div class="mt-6 flex justify-center">
            <div class="w-20 h-1 bg-red-600 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sección derecha: Formulario de login -->
    <div class="w-full md:w-1/2 flex items-center justify-center p-6 sm:p-8 lg:p-12">
      <div class="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden transition-all duration-300 transform hover:shadow-2xl">
        <!-- Encabezado -->
        <div class="px-8 pt-10 pb-6 text-center border-b border-gray-100">
          <h2 class="text-2xl sm:text-3xl font-bold text-gray-800">Iniciar Sesión</h2>
          <p class="mt-2 text-sm text-gray-500">Ingresa tus credenciales para acceder</p>
        </div>

        <!-- Formulario -->
        <form class="px-8 pt-6 pb-8" @submit.prevent="handleSubmit">
          <!-- Campo Usuario -->
          <div class="mb-5">
            <label for="username" class="sr-only">Usuario</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <input
                id="username"
                v-model="username"
                name="username"
                type="text"
                required
                placeholder="Tu usuario"
                class="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent text-base transition-all duration-200 placeholder-gray-400 text-gray-700"
              />
            </div>
          </div>

          <!-- Campo Contraseña -->
          <div class="mb-6">
            <label for="password" class="sr-only">Contraseña</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4" />
                </svg>
              </div>
              <input
                id="password"
                v-model="password"
                name="password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="Tu contraseña"
                class="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent text-base transition-all duration-200 placeholder-gray-400 text-gray-700"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-red-600 focus:outline-none"
              >
                <svg v-if="showPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7 1.274-4.057 5.064-7 9.542-7 .653 0 1.286.059 1.908.175l-2.31 2.31a4 4 0 00-5.512 5.512l-2.31 2.31zM15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Botón de envío -->
          <div class="mb-4">
            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 px-4 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 focus:ring-2 focus:ring-offset-2 focus:ring-red-500 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transition-all duration-300 ease-in-out disabled:opacity-75 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ loading ? 'Ingresando...' : 'Entrar' }}
            </button>
          </div>

          <!-- Mensaje de error -->
          <div v-if="error" class="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-start" role="alert">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-red-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ error }}</span>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)
const authStore = useAuthStore()

const handleSubmit = async () => {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
  } catch (err) {
    if (err.response?.status === 401) {
      error.value = 'Usuario o contraseña incorrectos.'
    } else {
      error.value = 'No se pudo conectar con el servidor. Intenta más tarde.'
    }
  } finally {
    loading.value = false
  }
}
</script>