<script setup>
import { cn } from "cn";

const props = defineProps({
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
});
</script>

<template>
  <div
    data-slot="empty-title"
    :class="
      cn('text-sm font-medium tracking-tight cn-font-heading', props.class)
    "
  >
    <slot />
  </div>
</template>
