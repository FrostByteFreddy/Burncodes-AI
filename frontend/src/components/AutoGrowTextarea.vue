<template>
  <textarea
    ref="textarea"
    :value="modelValue"
    @input="handleInput"
    class="resize-none overflow-hidden border-input focus-visible:border-ring focus-visible:ring-ring/50 rounded-lg border bg-card px-3 py-2 text-base transition-colors focus-visible:ring-3 flex min-h-16 w-full outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
    :rows="props.rows"
    :placeholder="props.placeholder"
  ></textarea>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';

const props = defineProps({
  modelValue: String,
  rows: [String, Number],
  placeholder: String,
});

const emit = defineEmits(['update:modelValue']);

const textarea = ref(null);

const autoGrow = (element) => {
  element.style.height = 'auto';
  element.style.height = `${element.scrollHeight}px`;
};

const handleInput = (event) => {
  emit('update:modelValue', event.target.value);
  autoGrow(event.target);
};

onMounted(() => {
  nextTick(() => {
    if (textarea.value) {
      autoGrow(textarea.value);
    }
  });
});

watch(() => props.modelValue, () => {
  nextTick(() => {
    if (textarea.value) {
      autoGrow(textarea.value);
    }
  });
});
</script>