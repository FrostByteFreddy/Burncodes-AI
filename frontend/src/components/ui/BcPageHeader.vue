<template>
  <header class="bc-pagehead">
    <div class="bc-pagehead__text">
      <div v-if="eyebrow || $slots.eyebrow" class="bc-pagehead__eyebrow"><slot name="eyebrow">{{ eyebrow }}</slot></div>
      <div class="bc-pagehead__titlerow">
        <h1 class="bc-pagehead__title">{{ title }}</h1>
        <slot name="status" />
      </div>
      <p v-if="lede" class="bc-pagehead__lede">{{ lede }}</p>
    </div>
    <div v-if="$slots.actions" class="bc-pagehead__actions"><slot name="actions" /></div>
  </header>
</template>

<script setup>
// Top of every dashboard page: title, status beside it, a one-line lede, actions on the right.
defineProps({ title: { type: String, required: true }, lede: { type: String, default: '' }, eyebrow: { type: String, default: '' } });
</script>
