<template>
  <div :class="['bc-progress', `bc-progress--${tone}`]">
    <div class="bc-progress__top">
      <span class="bc-progress__label">{{ label ?? $t('ui.of', { done: formatNumber(clamped), total: formatNumber(max) }) }}</span>
      <span v-if="!hidePercent" class="bc-progress__pct">{{ pct }} %</span>
    </div>
    <Progress :model-value="clamped" :max="max || 1" :class="['h-2 bg-muted', TONES[tone]]" />
    <div v-if="detail || $slots.detail" class="bc-progress__detail"><slot name="detail">{{ detail }}</slot></div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Progress } from './progress';
import { formatNumber } from '@/utils/format';

const TONES = {
  interactive: '*:data-[slot=progress-indicator]:bg-primary',
  ai: '*:data-[slot=progress-indicator]:bg-ai',
  ok: '*:data-[slot=progress-indicator]:bg-success',
};

// Honest progress: real counts, never a fake spinner. tone: interactive · ai (learning) · ok
const props = defineProps({
  value: { type: Number, default: 0 },
  max: { type: Number, default: 1 },
  label: { type: String, default: null },
  detail: { type: String, default: '' },
  tone: { type: String, default: 'interactive' },
  hidePercent: Boolean,
});
const clamped = computed(() => Math.max(0, Math.min(props.value, props.max || 1)));
const pct = computed(() => Math.round((clamped.value / (props.max || 1)) * 100));
</script>
