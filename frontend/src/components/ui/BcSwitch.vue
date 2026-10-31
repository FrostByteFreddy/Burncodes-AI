<template>
  <div v-if="label" class="bc-switchrow">
    <div class="bc-switchrow__text">
      <span :id="`${sid}-l`" class="bc-switchrow__title">{{ label }}</span>
      <span v-if="description" class="bc-switchrow__desc">{{ description }}</span>
    </div>
    <div class="bc-switchrow__ctl">
      <span v-if="stateText" class="bc-switchrow__state">{{ model ? (onText || $t('ui.on')) : (offText || $t('ui.off')) }}</span>
      <button :id="sid" type="button" role="switch" :aria-checked="model ? 'true' : 'false'" :aria-labelledby="`${sid}-l`"
        :class="['bc-switch', { 'is-on': model }]" :disabled="disabled" @click="toggle"><span class="bc-switch__knob"></span></button>
    </div>
  </div>
  <button v-else :id="sid" type="button" role="switch" :aria-checked="model ? 'true' : 'false'" :aria-label="ariaLabel"
    :class="['bc-switch', { 'is-on': model }]" :disabled="disabled" @click="toggle"><span class="bc-switch__knob"></span></button>
</template>

<script setup>
import { useFieldId } from './useFieldId';

defineProps({
  label: { type: String, default: '' }, description: { type: String, default: '' }, ariaLabel: { type: String, default: '' },
  onText: { type: String, default: '' }, offText: { type: String, default: '' }, stateText: { type: Boolean, default: true }, disabled: Boolean,
});
const model = defineModel({ type: Boolean, default: false });
const emit = defineEmits(['change']);
const sid = useFieldId('sw');
const toggle = () => { model.value = !model.value; emit('change', model.value); };
</script>
