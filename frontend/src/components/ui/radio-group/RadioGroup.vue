<script setup>
import { reactiveOmit } from "@vueuse/core";
import { cn } from "cn";
import { RadioGroupRoot, useForwardPropsEmits } from "reka-ui";

const props = defineProps({
  modelValue: { type: null, required: false },
  defaultValue: { type: null, required: false },
  disabled: { type: Boolean, required: false },
  orientation: { type: String, required: false },
  dir: { type: String, required: false },
  loop: { type: Boolean, required: false },
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false },
  name: { type: String, required: false },
  required: { type: Boolean, required: false },
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
});
const emits = defineEmits(["update:modelValue"]);

const delegatedProps = reactiveOmit(props, "class");

const forwarded = useForwardPropsEmits(delegatedProps, emits);
</script>

<template>
  <RadioGroupRoot
    v-slot="slotProps"
    data-slot="radio-group"
    :class="cn('grid gap-2 w-full', props.class)"
    v-bind="forwarded"
  >
    <slot v-bind="slotProps" />
  </RadioGroupRoot>
</template>
