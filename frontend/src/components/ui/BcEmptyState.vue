<template>
  <Empty :class="{ 'p-4': compact }">
    <EmptyHeader>
      <EmptyMedia v-if="icon" variant="icon"><BcIcon :name="icon" /></EmptyMedia>
      <EmptyTitle>{{ title }}</EmptyTitle>
      <EmptyDescription v-if="description">{{ description }}</EmptyDescription>
    </EmptyHeader>
    <EmptyContent v-if="$slots.action"><slot name="action" /></EmptyContent>
  </Empty>
</template>

<script setup>
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from './empty';
import BcIcon from './BcIcon.vue';

// Always names the next step
defineProps({ icon: { type: String, default: '' }, title: { type: String, required: true }, description: { type: String, default: '' }, compact: Boolean });
</script>
