<template>
  <div :class="['bc-seg', { 'bc-seg--sm': size === 'sm' }]" role="radiogroup" :aria-label="label || undefined">
    <button v-for="o in options" :key="o.value" type="button" role="radio" :aria-checked="model === o.value ? 'true' : 'false'"
      :class="['bc-seg__opt', { 'is-on': model === o.value }]" @click="model = o.value">
      <BcIcon v-if="o.icon" :name="o.icon" />{{ o.label }}
    </button>
  </div>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

defineProps({ options: { type: Array, required: true }, label: { type: String, default: '' }, size: { type: String, default: 'md' } });
const model = defineModel({ type: [String, Number], default: null });
</script>
