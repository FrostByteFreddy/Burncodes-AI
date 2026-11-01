<template>
  <Button :type="type" :variant="VARIANTS[variant] || variant" :size="SIZES[size] || size" :class="{ 'w-full': block }"
    :disabled="disabled || loading" :aria-busy="loading ? 'true' : undefined">
    <Spinner v-if="loading" data-icon="inline-start" />
    <BcIcon v-else-if="icon" :name="icon" data-icon="inline-start" />
    <span><slot /></span>
    <BcIcon v-if="iconRight && !loading" :name="iconRight" data-icon="inline-end" />
  </Button>
</template>

<script setup>
import { Button } from './button';
import { Spinner } from './spinner';
import BcIcon from './BcIcon.vue';

// The app's names for shadcn's button variants
const VARIANTS = { primary: 'default', secondary: 'outline', quiet: 'ghost' };
const SIZES = { md: 'default' };

// primary: the one main action · secondary · quiet · destructive (inside a confirmation) · destructive-quiet
defineProps({
  variant: { type: String, default: 'secondary' },
  size: { type: String, default: 'md' },
  type: { type: String, default: 'button' },
  icon: { type: String, default: '' },
  iconRight: { type: String, default: '' },
  loading: Boolean,
  disabled: Boolean,
  block: Boolean,
});
</script>
