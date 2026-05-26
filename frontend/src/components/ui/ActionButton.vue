<template>
  <component
    :is="to ? 'RouterLink' : 'button'"
    :to="to"
    :type="to ? undefined : type"
    :disabled="disabled"
    :class="[
      'ui-button',
      sizeClasses,
      variantClasses,
      disabled ? 'cursor-not-allowed opacity-60' : ''
    ]"
  >
    <slot />
  </component>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  to: { type: [String, Object], default: null },
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  disabled: { type: Boolean, default: false },
})

const variantClasses = computed(() => {
  if (props.variant === 'secondary') return 'ui-button-secondary'
  if (props.variant === 'ghost') return 'bg-transparent text-gray-700 hover:bg-gray-100'
  if (props.variant === 'danger') return 'bg-red-700 text-white hover:bg-red-800'
  return 'ui-button-primary'
})

const sizeClasses = computed(() => {
  if (props.size === 'sm') return 'px-3 py-2 text-sm'
  if (props.size === 'lg') return 'px-5 py-3 text-base'
  return 'px-4 py-2.5 text-sm'
})
</script>
