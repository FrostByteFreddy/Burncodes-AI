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
  <option
    data-slot="native-select-option"
    :class="cn('bg-[Canvas] text-[CanvasText]', props.class)"
  >
    <slot />
  </option>
</template>
