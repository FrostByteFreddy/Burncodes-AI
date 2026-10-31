<template>
  <label :class="['bc-checkrow', { 'is-disabled': disabled }]">
    <input v-model="model" type="checkbox" class="bc-checkbox" :disabled="disabled" />
    <span class="bc-checkrow__text">
      <span class="bc-checkrow__title">{{ title }}<span v-if="recommended" class="bc-tag">{{ $t('ui.recommended') }}</span></span>
      <span v-if="description" class="bc-checkrow__desc">{{ description }}</span>
    </span>
  </label>
</template>

<script setup>
defineProps({ title: { type: String, required: true }, description: { type: String, default: '' }, recommended: Boolean, disabled: Boolean });
const model = defineModel({ type: Boolean, default: false });
</script>
