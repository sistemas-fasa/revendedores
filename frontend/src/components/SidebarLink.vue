<script setup>
defineProps({
  to: { type: String, required: true },
  icon: { type: String, required: true },
  label: { type: String, required: true },
  badgeCount: { type: Number, default: 0 },
  linkClass: { type: String, default: '' }
})
</script>

<template>
  <RouterLink
    :to="to"
    :class="[
      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors',
      'text-gray-700 hover:bg-red-50 hover:text-red-700',
      linkClass
    ]"
    active-class="bg-red-50 text-red-800"
  >
    <i :class="['fa', icon, 'w-5 text-center text-xs']"></i>
    <span class="min-w-0 flex-1 truncate">{{ label }}</span>
    <span
      v-if="badgeCount > 0"
      class="ml-auto rounded-full bg-red-700 px-2 py-0.5 text-xs font-bold text-white"
    >{{ badgeCount }}</span>
  </RouterLink>
</template>
