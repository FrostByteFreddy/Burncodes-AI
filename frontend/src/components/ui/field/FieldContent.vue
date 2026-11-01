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
    data-slot="field-content"
    :class="
      cn(
        'gap-0.5 group/field-content flex flex-1 flex-col leading-snug',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
