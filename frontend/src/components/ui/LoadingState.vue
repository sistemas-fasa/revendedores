<template>
  <div class="ui-panel flex items-center justify-center gap-3 px-6 py-10 text-gray-600">
    <span class="h-5 w-5 animate-spin rounded-full border-2 border-red-700 border-t-transparent"></span>
    <span class="text-sm font-medium">{{ label }}</span>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: 'Cargando...' },
})
</script>
