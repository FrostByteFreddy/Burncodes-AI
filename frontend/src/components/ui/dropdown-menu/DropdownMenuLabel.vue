<script setup>
import { reactiveOmit } from "@vueuse/core";
import { cn } from "cn";
import { DropdownMenuLabel, useForwardProps } from "reka-ui";

const props = defineProps({
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false },
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
  inset: { type: Boolean, required: false },
});

const delegatedProps = reactiveOmit(props, "class", "inset");
const forwardedProps = useForwardProps(delegatedProps);
</script>

<template>
  <DropdownMenuLabel
    data-slot="dropdown-menu-label"
    :data-inset="inset ? '' : undefined"
    v-bind="forwardedProps"
    :class="
      cn(
        'text-muted-foreground px-1.5 py-1 text-xs font-medium data-inset:pl-7',
        props.class,
      )
    "
  >
    <slot />
  </DropdownMenuLabel>
</template>
