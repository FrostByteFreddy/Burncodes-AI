<template>
  <div class="swp" role="radiogroup" :aria-labelledby="labelId">
    <button
      v-for="c in palette"
      :key="c.id"
      type="button"
      role="radio"
      class="swp__dot"
      :class="{ 'swp__dot--active': modelValue === c.id }"
      :style="{ backgroundColor: c.value }"
      :aria-checked="modelValue === c.id"
      :title="nameOf(c)"
      :aria-label="nameOf(c)"
      @click="$emit('update:modelValue', c.id)"
    >
      <font-awesome-icon v-if="modelValue === c.id" :icon="['fas', 'check']" :style="{ color: checkColor(c.value) }" />
    </button>
  </div>
</template>

<script setup>
import { usePaletteNames, readableOn } from './palette';

defineProps({
  modelValue: { type: String, default: null },
  palette:    { type: Array, required: true },
  labelId:    { type: String, required: true },
});
defineEmits(['update:modelValue']);
const { nameOf } = usePaletteNames();
const checkColor = (hex) => readableOn(hex);
</script>

<style scoped>
.swp { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; }
.swp__dot {
  width: 32px; height: 32px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.18); cursor: pointer; font-size: 12px;
  transition: transform var(--t-fast);
}
.swp__dot:hover { transform: scale(1.08); }
.swp__dot--active { box-shadow: 0 0 0 2px var(--surface-1), 0 0 0 4px var(--interactive); }
</style>
