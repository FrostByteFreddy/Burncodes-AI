<template>
  <button :type="type" :class="['bc-btn', `bc-btn--${variant}`, `bc-btn--${size}`, { 'bc-btn--block': block, 'is-loading': loading }]"
    :disabled="disabled || loading" :aria-busy="loading ? 'true' : undefined">
    <span v-if="loading" class="bc-spinner" aria-hidden="true"></span>
    <BcIcon v-else-if="icon" :name="icon" />
    <span><slot /></span>
    <BcIcon v-if="iconRight && !loading" :name="iconRight" />
  </button>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

// primary: the one main action · secondary · quiet · destructive (inside a confirmation) · destructive-quiet
defineProps({
  variant: { type: String, default: 'secondary' },
  size: { type: String, default: 'md' },
  type: { type: String, default: 'button' },
  icon: { type: String, default: '' },
  iconRight: { type: String, default: '' },
  loading: Boolean,
  disabled: Boolean,
  block: Boolean,
});
</script>
