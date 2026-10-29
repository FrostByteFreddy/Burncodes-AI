<template>
  <div :class="['bc-balance', { 'is-low': low }]">
    <BcIcon :name="low ? 'triangle-exclamation' : 'wallet'" />
    <span class="bc-balance__label">{{ $t('ui.balance') }}</span>
    <span class="bc-balance__value">{{ formatCHF(amount) }}</span>
    <component :is="to ? 'router-link' : 'button'" v-if="topUp" :to="to || undefined" :type="to ? undefined : 'button'"
      class="bc-balance__action" @click="$emit('top-up')">{{ $t('ui.topUp') }}</component>
  </div>
</template>

<script setup>
import BcIcon from './BcIcon.vue';
import { formatCHF } from '@/utils/format';

defineProps({ amount: { type: Number, default: 0 }, low: Boolean, topUp: { type: Boolean, default: true }, to: { type: [String, Object], default: null } });
defineEmits(['top-up']);
</script>
