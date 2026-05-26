<script setup>
import SidebarLink from './SidebarLink.vue'
import { useAuthStore } from '@/stores/auth' // ✅ Importa el store
import { computed } from 'vue'

const props = defineProps({
  isSidebarOpen: { type: Boolean, required: true }
})

// ✅ Obténgo el store
const authStore = useAuthStore()

// ✅ Computed: ¿es staff?
const isStaff = computed(() => {
  return authStore.isAuthenticated && authStore.user && authStore.user.is_staff
})

const emit = defineEmits(['toggle'])

// Lista de ítems del menú con clases de Font Awesome
const menuItems = computed(() => {
  const discontinuedBadge = Number(authStore.discontinuedCount || 0)
  const offersBadge = Number(authStore.offersCount || 0)
  const items = [
    { to: '/dashboard', icon: 'fa-home', label: 'Dashboard' },
    { to: '/profile', icon: 'fa-user', label: 'Perfil' },
    { to: '/productos', icon: 'fa-box', label: 'Productos' },
    { to: '/productos?discontinuados=1', icon: 'fa-ban', label: 'Discontinuados', badgeCount: discontinuedBadge },
    { to: '/productos?oferta=1', icon: 'fa-tag', label: 'Ofertas', badgeCount: offersBadge },
    { to: '/pedidos', icon: 'fa-clipboard-list', label: 'Mis Pedidos' },
    { to: '/comprobantes', icon: 'fa-file-invoice', label: 'Comprobantes' },
  ]

  if (isStaff.value) {
    items.push({
      to: '/staff-dashboard',
      icon: 'fa-chart-line', // ícono de gráfico
      label: 'Panel de Staff',
      class: 'text-red-600 font-medium' // opcional: estilo especial
    })
    items.push({
      to: '/staff-carritos',
      icon: 'fa-shopping-cart', // ícono de carrito
      label: 'Carritos de Clientes',
      class: 'text-red-600 font-medium' // opcional: estilo especial
    })
    // Nuevo menú de Tracking (solo staff)
    items.push({
      to: '/staff/tracking',
      icon: 'fa-bullseye',
      label: 'Tracking (Campañas)',
      class: 'text-red-600 font-medium'
    })
    items.push({
      to: '/bot-test',
      icon: 'fa-comments',
      label: 'Bot de Prueba',
      class: 'text-red-600 font-medium'
    })
    items.push({
      to: '/staff/bot-report',
      icon: 'fa-clipboard-check',
      label: 'Reporte Bot',
      class: 'text-red-600 font-medium'
    })
  }

  return items
})

const isMobile = computed(() => window.innerWidth < 768)

const handleLinkClick = () => {
  if (isMobile.value && props.isSidebarOpen) {
    emit('toggle')
  }
}
</script>

<template>
  <aside
    :class="[
      'fixed md:static inset-y-0 flex flex-col w-64 bg-white shadow-lg transform transition-transform duration-300 z-40',
      isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center justify-center h-16 border-b px-6">
      <h1 class="text-xl font-bold text-red-600">Revendedores</h1>
    </div>

    <!-- Menú -->
    <nav class="flex-1 px-4 py-6 space-y-2">
      <SidebarLink
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        :icon="item.icon"
        :label="item.label"
        :badgeCount="item.badgeCount || 0"
        @click="handleLinkClick"
      />
    </nav>

    <!-- Cerrar en móvil -->
    <div class="p-4 border-t md:hidden">
      <button
        @click="$emit('toggle')"
        class="w-full text-left px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded"
      >
        Cerrar menú
      </button>
    </div>
  </aside>

  <!-- Overlay -->
  <div
    v-if="isSidebarOpen && isMobile"
    @click="$emit('toggle')"
    class="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
  ></div>
</template>
