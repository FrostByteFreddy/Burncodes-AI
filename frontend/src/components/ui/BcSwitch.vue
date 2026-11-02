<template>
  <div v-if="label" class="bc-switchrow">
    <div class="bc-switchrow__text">
      <span :id="`${sid}-l`" class="bc-switchrow__title">{{ label }}</span>
      <span v-if="description" class="bc-switchrow__desc">{{ description }}</span>
    </div>
    <div class="bc-switchrow__ctl">
      <span v-if="stateText" class="bc-switchrow__state">{{ model ? (onText || $t('ui.on')) : (offText || $t('ui.off')) }}</span>
      <Switch :id="sid" :model-value="model" :aria-labelledby="`${sid}-l`" :disabled="disabled" @update:model-value="toggle" />
    </div>
  </div>
  <Switch v-else :id="sid" :model-value="model" :aria-label="ariaLabel" :disabled="disabled" @update:model-value="toggle" />
</template>

<script setup>
import { Switch } from './switch';
import { useFieldId } from './useFieldId';

defineProps({
  label: { type: String, default: '' }, description: { type: String, default: '' }, ariaLabel: { type: String, default: '' },
  onText: { type: String, default: '' }, offText: { type: String, default: '' }, stateText: { type: Boolean, default: true }, disabled: Boolean,
});
const model = defineModel({ type: Boolean, default: false });
const emit = defineEmits(['change']);
const sid = useFieldId('sw');
const toggle = (value) => { model.value = value; emit('change', value); };
</script>
