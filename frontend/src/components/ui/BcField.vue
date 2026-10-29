<template>
  <div :class="['bc-field', { 'has-error': error }]">
    <label class="bc-field__label" :for="htmlFor || undefined">{{ label }}<span v-if="optional" class="bc-field__opt"> {{ $t('ui.optional') }}</span></label>
    <slot />
    <div v-if="error" class="bc-field__error" :id="htmlFor ? `${htmlFor}-err` : undefined"><BcIcon name="circle-exclamation" />{{ error }}</div>
    <div v-else-if="hint" class="bc-field__hint" :id="htmlFor ? `${htmlFor}-hint` : undefined">{{ hint }}</div>
  </div>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

// One short hint line at most; an error says how to fix it.
defineProps({ label: { type: String, required: true }, htmlFor: { type: String, default: '' }, hint: { type: String, default: '' }, error: { type: String, default: '' }, optional: Boolean });
</script>
