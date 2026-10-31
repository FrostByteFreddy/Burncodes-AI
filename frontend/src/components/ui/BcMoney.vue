<template>
  <span :class="['bc-money', `bc-money--${size}`, { 'is-estimate': estimate, [`bc-money--${tone}`]: tone }]">
    <span v-if="estimate" class="bc-money__ca">{{ `${$t('ui.ca')}\u00a0` }}</span>{{ formatCHF(amount) }}
  </span>
</template>

<script setup>
import { formatCHF } from '@/utils/format';

// "CHF 18.40"; estimates read "ca. CHF 18.40". size: body · strong · figure-sm · figure
defineProps({
  amount: { type: Number, default: 0 },
  estimate: Boolean,
  size: { type: String, default: 'body' },
  tone: { type: String, default: '' },
});
</script>
