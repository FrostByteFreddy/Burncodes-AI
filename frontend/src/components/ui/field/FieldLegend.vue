<script setup>
import { cn } from "cn";

const props = defineProps({
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
  variant: { type: String, required: false, default: "legend" },
});
</script>

<template>
  <legend
    data-slot="field-legend"
    :data-variant="variant"
    :class="
      cn(
        'mb-1.5 font-medium data-[variant=label]:text-sm data-[variant=legend]:text-base',
        props.class,
      )
    "
  >
    <slot />
  </legend>
</template>
