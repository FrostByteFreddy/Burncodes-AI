<script setup>
import { reactiveOmit } from "@vueuse/core";
import { cn } from "cn";
import { ProgressIndicator, ProgressRoot } from "reka-ui";

const props = defineProps({
  modelValue: { type: [Number, null], required: false, default: 0 },
  max: { type: Number, required: false },
  getValueLabel: { type: Function, required: false },
  getValueText: { type: Function, required: false },
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false },
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
});

const delegatedProps = reactiveOmit(props, "class");
</script>

<template>
  <ProgressRoot
    data-slot="progress"
    v-bind="delegatedProps"
    :class="
      cn(
        'bg-muted h-1 rounded-full relative flex w-full items-center overflow-x-hidden',
        props.class,
      )
    "
  >
    <ProgressIndicator
      data-slot="progress-indicator"
      class="bg-primary size-full flex-1 transition-all"
      :style="`transform: translateX(-${100 - (props.modelValue ?? 0)}%);`"
    />
  </ProgressRoot>
</template>
