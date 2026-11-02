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
  <optgroup
    data-slot="native-select-optgroup"
    :class="cn('bg-[Canvas] text-[CanvasText]', props.class)"
  >
    <slot />
  </optgroup>
</template>
