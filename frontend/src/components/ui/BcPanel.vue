<template>
  <Card :as="as" :class="{ 'gap-0 py-0': flush }">
    <CardHeader v-if="title || description || $slots.actions" :class="{ 'py-6': flush }">
      <CardTitle v-if="title">{{ title }}</CardTitle>
      <CardDescription v-if="description">{{ description }}</CardDescription>
      <CardAction v-if="$slots.actions"><slot name="actions" /></CardAction>
    </CardHeader>
    <CardContent :class="{ 'px-0': flush }"><slot /></CardContent>
  </Card>
</template>

<script setup>
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from './card';

// One object (figures, a list with a header). Never a panel inside a panel.
defineProps({ title: { type: String, default: '' }, description: { type: String, default: '' }, flush: Boolean, as: { type: String, default: 'div' } });
</script>
