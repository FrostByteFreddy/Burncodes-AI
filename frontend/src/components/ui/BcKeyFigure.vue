<template>
  <div class="bc-kf">
    <div class="bc-kf__label">{{ label }}</div>
    <div :class="['bc-kf__value', { 'bc-kf__value--sm': size === 'sm' }]"><slot name="value">{{ value }}</slot></div>
    <div v-if="delta != null" :class="['bc-kf__delta', delta > 0 ? 'is-up' : delta < 0 ? 'is-down' : 'is-flat']">
      <BcIcon :name="delta > 0 ? 'arrow-up' : delta < 0 ? 'arrow-down' : 'minus'" />
      <span>{{ delta > 0 ? '+' : delta < 0 ? '−' : '±' }}{{ Math.abs(delta) }} % {{ deltaLabel || $t('ui.vsPrevious') }}</span>
    </div>
    <div v-if="hint" class="bc-kf__hint">{{ hint }}</div>
    <slot name="action" />
  </div>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  delta: { type: Number, default: null },
  deltaLabel: { type: String, default: '' },
  hint: { type: String, default: '' },
  size: { type: String, default: 'md' },
});
</script>
