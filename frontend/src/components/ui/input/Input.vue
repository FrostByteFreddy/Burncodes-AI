<script setup>
import { useVModel } from "@vueuse/core";
import { ref } from "vue";
import { cn } from "cn";

const props = defineProps({
  defaultValue: { type: [String, Number], required: false },
  modelValue: { type: [String, Number], required: false },
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
});

const emits = defineEmits(["update:modelValue"]);

const modelValue = useVModel(props, "modelValue", emits, {
  passive: true,
  defaultValue: props.defaultValue,
});

// Parents can still focus and select the field through a ref
const el = ref(null);
defineExpose({ focus: () => el.value?.focus(), select: () => el.value?.select() });
</script>

<template>
  <input
    ref="el"
    v-model="modelValue"
    data-slot="input"
    :class="
      cn(
        'dark:bg-card border-input focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:aria-invalid:border-destructive/50 disabled:bg-muted h-10 rounded-md border bg-card px-3 py-1 text-base transition-colors file:h-6 file:text-sm file:font-medium focus-visible:ring-3 aria-invalid:ring-3 w-full min-w-0 outline-none file:inline-flex file:border-0 file:bg-transparent file:text-foreground placeholder:text-muted-foreground disabled:pointer-events-none disabled:cursor-not-allowed disabled:text-muted-foreground',
        props.class,
      )
    "
  />
</template>
