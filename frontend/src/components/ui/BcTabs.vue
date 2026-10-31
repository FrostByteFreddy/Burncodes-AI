<template>
  <div class="bc-tabs" role="tablist" :aria-label="label || undefined">
    <button v-for="t in tabs" :key="t.id" type="button" role="tab" :aria-selected="model === t.id ? 'true' : 'false'" :tabindex="model === t.id ? 0 : -1"
      :class="['bc-tab', { 'is-on': model === t.id }]" @click="model = t.id">
      {{ t.label }}<span v-if="t.count != null" class="bc-tab__count">{{ formatNumber(t.count) }}</span>
    </button>
  </div>
</template>

<script setup>
import { formatNumber } from '@/utils/format';

defineProps({ tabs: { type: Array, required: true }, label: { type: String, default: '' } });
const model = defineModel({ type: String, default: '' });
</script>
