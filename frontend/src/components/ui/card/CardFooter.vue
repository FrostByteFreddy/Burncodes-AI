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
    data-slot="card-footer"
    :class="
      cn(
        'rounded-b-xl border-t px-6 pt-4 group-data-[size=sm]/card:p-3 flex items-center',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
