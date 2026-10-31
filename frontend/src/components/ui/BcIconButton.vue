<template>
  <button type="button" :class="['bc-iconbtn', `bc-iconbtn--${variant}`, `bc-iconbtn--${size}`]" :aria-label="label" :title="label">
    <BcIcon :name="icon" />
  </button>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

defineProps({
  icon: { type: String, required: true },
  label: { type: String, required: true },
  variant: { type: String, default: 'quiet' },
  size: { type: String, default: 'md' },
});
</script>
