<template>
  <div :class="['bc-panel', { 'bc-panel--flush': flush }]">
    <div v-if="title" class="bc-panel__head">
      <h3 class="bc-panel__title">{{ title }}</h3>
      <slot name="actions" />
    </div>
    <slot />
  </div>
</template>

<script setup>
// One object (figures, a list with a header). Never a panel inside a panel.
defineProps({ title: { type: String, default: '' }, flush: Boolean });
</script>
