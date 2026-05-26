// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Swal from 'sweetalert2'
import { useAuthStore } from '@/stores/auth'

// Lazy loading de todos los componentes para mejor rendimiento
const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { layout: 'auth' }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/profile', 
    component: () => import('@/views/UserProfile.vue'), 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/productos', 
    component: () => import('@/views/ArticulosView.vue'), 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/carrito', 
    component: () => import('@/views/CarritoView.vue'), 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/pedidos', 
    component: () => import('@/views/PedidosView.vue'), 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/comprobantes', 
    name: 'comprobantes',
    component: () => import('@/views/ComprobantesView.vue'), 
    meta: { requiresAuth: true } 
  },
  {
    path: '/bot-test',
    name: 'bot-test',
    component: () => import('@/views/BotTestChat.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  {
    path: '/staff/bot-report',
    name: 'staff-bot-report',
    component: () => import('@/views/StaffBotReport.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  { 
    path: '/pedido-confirmado/:id?', 
    name: 'pedido-confirmado',
    component: () => import('@/views/PedidoConfirmado.vue'), 
    meta: { requiresAuth: true } 
  },
  {
    path: '/staff-dashboard',
    name: 'staff-dashboard',
    component: () => import('@/views/StaffDashboard.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  {
    path: '/staff-carritos',
    name: 'staff-carritos',
    component: () => import('@/views/StaffCarritosView.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  {
    path: '/staff/tracking',
    name: 'staff-tracking',
    component: () => import('@/views/StaffTracking.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  {
    path: '/',
    redirect: '/productos'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Guardia de navegación
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresStaff && (!authStore.isAuthenticated || !authStore.user || !authStore.user.is_staff)) {
    // If route requires staff and user is not authenticated or not staff
    Swal.fire({ icon: 'error', title: 'Acceso denegado', text: 'Solo el personal autorizado puede acceder a esta área.' })
    next('/productos'); // Redirect to the main buying surface
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next('/productos')
  } else {
    next()
  }
})

export default router
