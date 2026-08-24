<template>
  <div class="flex h-screen flex-col bg-gray-100">
    <Navbar @toggleSidebar="toggleSidebar" />

    <div class="flex min-h-0 flex-1 overflow-hidden" :class="{ 'sidebar-mobile-open': isSidebarOpen && isMobile }">
      <Sidebar
        :isSidebarOpen="isSidebarOpen"
        @toggle="toggleSidebar"
      />

      <main class="min-w-0 flex-1 overflow-y-auto bg-gray-100 p-4 sm:p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, provide } from 'vue'
import Navbar from '@/components/Navbar.vue'
import Sidebar from '@/components/Sidebar.vue'

const isSidebarOpen = ref(window.innerWidth >= 768)
const isMobile = ref(window.innerWidth < 768)
provide('isSidebarOpen', isSidebarOpen)
provide('isMobile', isMobile)

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const syncSidebarWithViewport = () => {
  isSidebarOpen.value = window.innerWidth >= 768
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  window.addEventListener('resize', syncSidebarWithViewport)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncSidebarWithViewport)
})
</script>
