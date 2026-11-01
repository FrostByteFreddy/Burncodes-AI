<script setup>
import { cn } from "cn";
import { Separator } from '@/components/ui/separator';

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
    data-slot="field-separator"
    :data-content="!!$slots.default"
    :class="
      cn(
        '-my-2 h-5 text-sm group-data-[variant=outline]/field-group:-mb-2 relative',
        props.class,
      )
    "
  >
    <Separator class="absolute inset-0 top-1/2" />
    <span
      v-if="$slots.default"
      class="text-muted-foreground px-2 relative mx-auto block w-fit bg-background"
      data-slot="field-separator-content"
    >
      <slot />
    </span>
  </div>
</template>
