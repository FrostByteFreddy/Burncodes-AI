<template>
  <Card :as="as" :class="['block gap-0 rounded-lg py-0 text-base ring-0 border shadow-none', flush ? 'overflow-hidden' : 'p-6']">
    <div v-if="title" :class="['flex items-center justify-between gap-4', flush ? 'p-6 pb-4' : 'mb-5']">
      <CardTitle class="text-lg leading-[26px] font-bold">{{ title }}</CardTitle>
      <slot name="actions" />
    </div>
    <slot />
  </Card>
</template>

<script setup>
import { Card, CardTitle } from './card';

// One object (figures, a list with a header). Never a panel inside a panel.
defineProps({ title: { type: String, default: '' }, flush: Boolean, as: { type: String, default: 'div' } });
</script>
