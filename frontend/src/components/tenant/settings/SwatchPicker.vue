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
    <label v-if="allowCustom" class="swp__dot swp__custom" :title="$t('configure.edit.custom')">
      <font-awesome-icon :icon="['fas', 'plus']" />
      <input type="color" class="swp__custom-input" :aria-label="$t('configure.edit.custom')" @change="$emit('custom', $event.target.value)" />
    </label>
  </div>
</template>

<script setup>
import { usePaletteNames, readableOn } from './palette';

defineProps({
  modelValue: { type: String, default: null },
  palette:    { type: Array, required: true },
  labelId:    { type: String, required: true },
  allowCustom: { type: Boolean, default: false },
});
defineEmits(['update:modelValue', 'custom']);
const { nameOf } = usePaletteNames();
const checkColor = (hex) => readableOn(hex);
</script>

<style scoped>
.swp { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.swp__dot {
  width: 32px; height: 32px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid var(--border-strong); cursor: pointer; font-size: 12px;
  transition: transform var(--t-fast);
}
.swp__dot:hover { transform: scale(1.08); }
.swp__custom { position: relative; background: var(--surface-2); color: var(--surface-muted); border-style: dashed; }
.swp__custom:hover { color: var(--surface-heading); }
.swp__custom:focus-within { box-shadow: var(--focus-ring-shadow); }
.swp__custom-input { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
.swp__dot--active { box-shadow: 0 0 0 2px var(--surface-1), 0 0 0 4px var(--interactive); }
</style>
