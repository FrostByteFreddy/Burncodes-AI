<template>
  <textarea
    ref="textarea"
    :value="modelValue"
    @input="handleInput"
    class="resize-none overflow-hidden"
  ></textarea>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';

const props = defineProps({
  modelValue: String,
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
