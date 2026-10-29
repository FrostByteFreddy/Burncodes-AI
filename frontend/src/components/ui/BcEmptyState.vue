<template>
  <div :class="['bc-empty', { 'bc-empty--compact': compact }]">
    <span v-if="icon" class="bc-empty__icon"><BcIcon :name="icon" /></span>
    <h3 class="bc-empty__title">{{ title }}</h3>
    <p v-if="description" class="bc-empty__desc">{{ description }}</p>
    <div v-if="$slots.action" class="bc-empty__action"><slot name="action" /></div>
  </div>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

// Always names the next step
defineProps({ icon: { type: String, default: '' }, title: { type: String, required: true }, description: { type: String, default: '' }, compact: Boolean });
</script>
