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
    data-slot="card-description"
    :class="cn('text-muted-foreground text-base max-w-(--reading-max)', props.class)"
  >
    <slot />
  </div>
</template>
