<template>
  <div class="h-screen flex flex-col">
    <!-- Navbar fijo arriba -->
    <Navbar @toggleSidebar="toggleSidebar" />

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <Sidebar
        :isSidebarOpen="isSidebarOpen"
        @toggle="toggleSidebar"
      />

      <!-- Contenido principal -->
      <main class="flex-1 overflow-y-auto bg-gray-50 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import Navbar from "@/components/Navbar.vue"
import Sidebar from "@/components/Sidebar.vue"
import OffersModal from '@/components/OffersModal.vue'

const isSidebarOpen = ref(window.innerWidth >= 768)

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}
</script>

<style>
/* Puedes ajustar según tu diseño */
</style>
