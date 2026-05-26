<template>
  <div class="flex h-screen flex-col bg-gray-100">
    <Navbar @toggleSidebar="toggleSidebar" />

    <div class="flex min-h-0 flex-1 overflow-hidden">
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
import { onMounted, onUnmounted, ref } from 'vue'
import Navbar from '@/components/Navbar.vue'
import Sidebar from '@/components/Sidebar.vue'

const isSidebarOpen = ref(window.innerWidth >= 768)

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const syncSidebarWithViewport = () => {
  isSidebarOpen.value = window.innerWidth >= 768
}

onMounted(() => {
  window.addEventListener('resize', syncSidebarWithViewport)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncSidebarWithViewport)
})
</script>
