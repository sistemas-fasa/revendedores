<template>
  <section class="ui-panel px-6 py-12 text-center">
    <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-700">
      <slot name="icon">
        <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V7a2 2 0 00-2-2h-3.5L12 3 9.5 5H6a2 2 0 00-2 2v6m16 0v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4m16 0H4" />
        </svg>
      </slot>
    </div>
    <h2 class="text-lg font-bold text-gray-950">{{ title }}</h2>
    <p v-if="description" class="mx-auto mt-2 max-w-md text-sm leading-6 text-gray-600">{{ description }}</p>
    <div v-if="$slots.actions" class="mt-5 flex justify-center gap-2">
      <slot name="actions" />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>
