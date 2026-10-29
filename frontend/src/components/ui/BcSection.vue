<template>
  <section class="bc-section">
    <div v-if="title || $slots.actions" class="bc-section__head">
      <div>
        <component :is="level === 3 ? 'h3' : 'h2'" v-if="title" :class="level === 3 ? 'bc-section__title3' : 'bc-section__title'">{{ title }}</component>
        <p v-if="description" class="bc-section__desc">{{ description }}</p>
      </div>
      <div v-if="$slots.actions" class="bc-section__actions"><slot name="actions" /></div>
    </div>
    <slot />
  </section>
</template>

<script setup>
// A titled region of a page, separated by space rather than boxes.
defineProps({ title: { type: String, default: '' }, description: { type: String, default: '' }, level: { type: Number, default: 2 } });
</script>
