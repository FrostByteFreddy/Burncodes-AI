<template>
  <Button type="button" :variant="VARIANTS[variant] || variant" :size="SIZES[size] || 'icon'" :aria-label="label" :title="label">
    <BcIcon :name="icon" />
  </Button>
</template>

<script setup>
import { Button } from './button';
import BcIcon from './BcIcon.vue';

const VARIANTS = { primary: 'default', secondary: 'outline', quiet: 'ghost', danger: 'destructive-quiet' };
const SIZES = { sm: 'icon-sm', md: 'icon', lg: 'icon-lg' };

defineProps({
  icon: { type: String, required: true },
  label: { type: String, required: true },
  variant: { type: String, default: 'quiet' },
  size: { type: String, default: 'md' },
});
</script>
