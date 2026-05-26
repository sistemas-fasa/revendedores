<!-- App.vue -->
<template>
  <!-- 1. Layout dinámico -->
  <component :is="layout">
    <router-view />
    <PWAInstaller /> <!-- Agrega el componente de instalación -->
  </component>

</template>

<script setup>
// ✅ 1. Importa el componente correctamente
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import PWAInstaller from './components/PWAInstaller.vue'

// ✅ 2. Importa layouts
import MainLayout from './layouts/MainLayout.vue';
import AuthLayout from './layouts/AuthLayout.vue';

// ✅ 3. Calcula layout desde el route
const route = useRoute();

const layout = computed(() => {
  return route.meta.layout === 'auth' ? AuthLayout : MainLayout;
});

// export default removed because <script setup> provides the component definition
</script>

<style>
/* Estilo base */
body {
  margin: 0;
  font-family: 'Inter', 'Segoe UI', sans-serif;
}
</style>
