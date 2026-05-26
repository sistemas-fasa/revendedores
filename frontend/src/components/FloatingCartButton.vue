<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { cart } from '@/services/cart'

// Posición del botón (inicialmente en la esquina inferior derecha)
const position = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const buttonRef = ref(null)
const hasMoved = ref(false)

// Cargar posición guardada del localStorage
const loadPosition = () => {
  const saved = localStorage.getItem('floatingCartPosition')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      position.value = parsed
    } catch (e) {
      // Si hay error, usar posición por defecto
      setDefaultPosition()
    }
  } else {
    setDefaultPosition()
  }
}

// Establecer posición por defecto (esquina inferior derecha)
const setDefaultPosition = () => {
  position.value = {
    x: window.innerWidth - 80,
    y: window.innerHeight - 80
  }
}

// Guardar posición en localStorage
const savePosition = () => {
  localStorage.setItem('floatingCartPosition', JSON.stringify(position.value))
}

// Mantener el botón dentro de los límites de la pantalla
const constrainPosition = () => {
  const buttonSize = 64 // Tamaño aproximado del botón
  const padding = 10
  
  position.value.x = Math.max(padding, Math.min(position.value.x, window.innerWidth - buttonSize - padding))
  position.value.y = Math.max(padding, Math.min(position.value.y, window.innerHeight - buttonSize - padding))
}

// Eventos de mouse/touch para arrastrar
const startDrag = (e) => {
  isDragging.value = true
  hasMoved.value = false
  
  const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY
  
  dragOffset.value = {
    x: clientX - position.value.x,
    y: clientY - position.value.y
  }
  
  // Prevenir scroll en móvil mientras arrastramos
  if (e.type.includes('touch')) {
    e.preventDefault()
  }
}

const onDrag = (e) => {
  if (!isDragging.value) return
  
  const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY
  
  const newX = clientX - dragOffset.value.x
  const newY = clientY - dragOffset.value.y
  
  // Detectar si se movió significativamente
  if (Math.abs(newX - position.value.x) > 5 || Math.abs(newY - position.value.y) > 5) {
    hasMoved.value = true
  }
  
  position.value = { x: newX, y: newY }
  constrainPosition()
}

const endDrag = () => {
  if (isDragging.value) {
    isDragging.value = false
    savePosition()
  }
}

// Manejar click/tap - solo navegar si no se arrastró
const handleClick = (e) => {
  if (hasMoved.value) {
    e.preventDefault()
    e.stopPropagation()
  }
}

// Manejar redimensionamiento de ventana
const handleResize = () => {
  constrainPosition()
  savePosition()
}

onMounted(() => {
  loadPosition()
  
  // Eventos globales para arrastrar
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', endDrag)
  window.addEventListener('touchmove', onDrag, { passive: false })
  window.addEventListener('touchend', endDrag)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', endDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('touchend', endDrag)
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div 
    ref="buttonRef"
    class="fixed z-40 select-none"
    :style="{ 
      left: position.x + 'px', 
      top: position.y + 'px',
      cursor: isDragging ? 'grabbing' : 'grab'
    }"
    @mousedown="startDrag"
    @touchstart="startDrag"
  >
    <router-link 
      to="/carrito" 
      @click="handleClick"
      class="bg-red-600 text-white px-4 py-4 rounded-full shadow-lg hover:bg-red-700 transition flex items-center justify-center relative"
      :class="{ 'pointer-events-none': hasMoved && isDragging }"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <span 
        v-if="cart.totalItems > 0" 
        class="absolute -top-2 -right-2 bg-red-700 text-white text-xs rounded-full h-6 w-6 flex items-center justify-center"
      >
        {{ cart.totalItems }}
      </span>
    </router-link>
    
    <!-- Indicador visual de arrastre -->
    <div 
      v-if="isDragging" 
      class="absolute inset-0 rounded-full ring-4 ring-red-300 ring-opacity-50 animate-pulse pointer-events-none"
    ></div>
  </div>
</template>

<style scoped>
/* Transición suave cuando no se está arrastrando */
.fixed:not(:active) {
  transition: box-shadow 0.2s ease;
}
</style>
