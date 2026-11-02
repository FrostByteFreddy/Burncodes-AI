<script setup>
import { cn } from "cn";

const props = defineProps({
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
  size: { type: String, required: false, default: "default" },
  as: { type: String, required: false, default: "div" },
});
</script>

<template>
  <component
    :is="as"
    data-slot="card"
    :data-size="size"
    :class="
      cn(
        'bg-card text-card-foreground gap-5 rounded-xl border py-6 text-base group/card flex flex-col',
        props.class,
      )
    "
  >
    <slot />
  </component>
</template>
