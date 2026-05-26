<template>
  <span :class="['inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold', toneClasses]">
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tone: { type: String, default: 'neutral' },
})

const toneClasses = computed(() => {
  const tones = {
    neutral: 'bg-gray-100 text-gray-700',
    primary: 'bg-red-100 text-red-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-amber-100 text-amber-800',
    danger: 'bg-red-700 text-white',
    info: 'bg-blue-100 text-blue-800',
  }
  return tones[props.tone] || tones.neutral
})
</script>
