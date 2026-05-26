<template>
  <div class="ui-table-wrap">
    <table class="ui-table">
      <thead v-if="$slots.head">
        <slot name="head" />
      </thead>
      <tbody>
        <slot />
      </tbody>
    </table>
  </div>
</template>
