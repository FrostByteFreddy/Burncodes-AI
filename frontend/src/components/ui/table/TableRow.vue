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
  <tr
    data-slot="table-row"
    :class="
      cn(
        'hover:bg-muted/50 data-[state=selected]:bg-muted border-b transition-colors has-aria-expanded:bg-muted/50',
        props.class,
      )
    "
  >
    <slot />
  </tr>
</template>
