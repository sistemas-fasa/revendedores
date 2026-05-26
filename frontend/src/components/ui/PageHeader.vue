<template>
  <header class="ui-panel p-4 sm:p-5">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div class="min-w-0">
        <p v-if="eyebrow" class="text-xs font-bold uppercase text-red-700">{{ eyebrow }}</p>
        <h1 class="mt-1 text-2xl font-bold leading-tight text-gray-950 sm:text-3xl">{{ title }}</h1>
        <p v-if="description" class="mt-2 max-w-3xl text-sm leading-6 text-gray-600">{{ description }}</p>
      </div>
      <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  eyebrow: { type: String, default: '' },
})
</script>
