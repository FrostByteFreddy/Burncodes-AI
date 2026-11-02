<template>
  <div v-if="variant === 'text'" class="bc-skel-group" aria-hidden="true">
    <Skeleton v-for="i in lines" :key="i" class="bc-skel--line" :style="{ width: i === lines ? '60%' : '100%' }" />
  </div>
  <Skeleton v-else :class="`bc-skel--${variant}`" :style="{ width: size(width), height: size(height) }" aria-hidden="true" />
</template>

<script setup>
import { Skeleton } from './skeleton';

// Loading placeholder in the real layout. variant: text · figure · block · circle
defineProps({ variant: { type: String, default: 'text' }, lines: { type: Number, default: 3 }, width: { type: [String, Number], default: null }, height: { type: [String, Number], default: null } });
const size = (v) => (typeof v === 'number' ? `${v}px` : v || undefined);
</script>
