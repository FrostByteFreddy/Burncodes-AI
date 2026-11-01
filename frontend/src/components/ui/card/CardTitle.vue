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
    data-slot="card-title"
    :class="
      cn(
        'text-lg leading-[26px] font-bold',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
