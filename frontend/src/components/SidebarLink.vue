<script setup>
defineProps({
  to: { type: String, required: true },
  icon: { type: String, required: true },
  label: { type: String, required: true },
  badgeCount: { type: Number, default: 0 },
  linkClass: { type: String, default: '' } // ✅ Clase opcional
})
</script>

<template>
  <RouterLink
    :to="to"
    :class="[
      'flex items-center gap-3 px-4 py-2.5 text-sm rounded-lg transition-colors',
      'text-gray-700 hover:bg-red-50 hover:text-red-600',
      linkClass // ✅ Aplica clase personalizada
    ]"
  >
    <i :class="['fa', icon]"></i>
    <span>{{ label }}</span>
    <span
      v-if="badgeCount > 0"
      class="ml-auto bg-red-600 text-white text-xs font-semibold px-2 py-0.5 rounded-full"
    >{{ badgeCount }}</span>
  </RouterLink>
</template>