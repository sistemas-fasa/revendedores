<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import SidebarLink from './SidebarLink.vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  isSidebarOpen: { type: Boolean, required: true }
})

const emit = defineEmits(['toggle'])
const authStore = useAuthStore()

const isStaff = computed(() => {
  return authStore.isAuthenticated && authStore.user && authStore.user.is_staff
})

const shoppingItems = computed(() => {
  const discontinuedBadge = Number(authStore.discontinuedCount || 0)
  const offersBadge = Number(authStore.offersCount || 0)

  return [
    { to: '/productos', icon: 'fa-search', label: 'Buscar artículos' },
    { to: '/productos?oferta=1', icon: 'fa-tag', label: 'Ofertas', badgeCount: offersBadge },
    { to: '/productos?discontinuados=1', icon: 'fa-ban', label: 'Discontinuados', badgeCount: discontinuedBadge },
    { to: '/pedidos', icon: 'fa-clipboard-list', label: 'Mis Pedidos' },
  ]
})

const accountItems = [
  { to: '/dashboard', icon: 'fa-chart-pie', label: 'Resumen de cuenta' },
  { to: '/comprobantes', icon: 'fa-file-invoice', label: 'Comprobantes' },
  { to: '/profile', icon: 'fa-user', label: 'Perfil' },
]

const staffItems = computed(() => {
  if (!isStaff.value) return []

  return [
    { to: '/staff-dashboard', icon: 'fa-chart-line', label: 'Panel de Staff' },
    { to: '/staff-carritos', icon: 'fa-shopping-cart', label: 'Carritos de Clientes' },
    { to: '/staff/tracking', icon: 'fa-bullseye', label: 'Tracking' },
    { to: '/bot-test', icon: 'fa-comments', label: 'Bot de Prueba' },
    { to: '/staff/bot-report', icon: 'fa-clipboard-check', label: 'Reporte Bot' },
  ]
})

const isMobile = ref(window.innerWidth < 768)

const syncViewport = () => {
  isMobile.value = window.innerWidth < 768
}

const handleLinkClick = () => {
  if (isMobile.value && props.isSidebarOpen) {
    emit('toggle')
  }
}

onMounted(() => {
  window.addEventListener('resize', syncViewport)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncViewport)
})
</script>

<template>
  <aside
    :class="[
      'fixed inset-y-0 z-40 flex w-72 flex-col border-r border-gray-200 bg-white shadow-xl transition-transform duration-300 md:static md:w-64 md:shadow-none',
      isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
    ]"
  >
    <div class="flex h-16 items-center border-b px-5">
      <div>
        <h1 class="text-lg font-black text-red-700">Revendedores</h1>
        <p class="text-xs text-gray-500">Comprar, revisar y repetir</p>
      </div>
    </div>

    <nav class="flex-1 space-y-6 overflow-y-auto px-3 py-5">
      <section>
        <p class="px-3 text-xs font-bold uppercase text-gray-400">Comprar</p>
        <div class="mt-2 space-y-1">
          <SidebarLink
            v-for="item in shoppingItems"
            :key="item.to"
            :to="item.to"
            :icon="item.icon"
            :label="item.label"
            :badgeCount="item.badgeCount || 0"
            @click="handleLinkClick"
          />
        </div>
      </section>

      <section>
        <p class="px-3 text-xs font-bold uppercase text-gray-400">Cuenta</p>
        <div class="mt-2 space-y-1">
          <SidebarLink
            v-for="item in accountItems"
            :key="item.to"
            :to="item.to"
            :icon="item.icon"
            :label="item.label"
            @click="handleLinkClick"
          />
        </div>
      </section>

      <section v-if="staffItems.length">
        <p class="px-3 text-xs font-bold uppercase text-gray-400">Staff</p>
        <div class="mt-2 space-y-1">
          <SidebarLink
            v-for="item in staffItems"
            :key="item.to"
            :to="item.to"
            :icon="item.icon"
            :label="item.label"
            linkClass="text-red-700"
            @click="handleLinkClick"
          />
        </div>
      </section>
    </nav>

    <div class="border-t p-4 md:hidden">
      <button
        @click="$emit('toggle')"
        class="ui-button ui-button-secondary w-full px-4 py-2 text-sm"
      >
        Cerrar menú
      </button>
    </div>
  </aside>

  <div
    v-if="isSidebarOpen && isMobile"
    @click="$emit('toggle')"
    class="fixed inset-0 z-30 bg-black/40 md:hidden"
  ></div>
</template>
