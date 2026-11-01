<template>
  <fieldset :class="['bc-radiocards', { 'bc-radiocards--stack': columns === 1 }]">
    <legend v-if="legend" class="bc-field__label">{{ legend }}</legend>
    <RadioGroup v-model="model" class="bc-radiocards__grid">
      <label v-for="o in options" :key="o.value" :class="['bc-radiocard', { 'is-checked': model === o.value, 'is-disabled': o.disabled }]">
        <RadioGroupItem :value="o.value" :disabled="o.disabled" class="mt-0.5 size-5" />
        <span v-if="o.icon" class="bc-radiocard__icon"><BcIcon :name="o.icon" /></span>
        <span class="bc-radiocard__text">
          <span class="bc-radiocard__title">{{ o.title }}<span v-if="o.badge" class="bc-radiocard__badge">{{ o.badge }}</span></span>
          <span v-if="o.description" class="bc-radiocard__desc">{{ o.description }}</span>
        </span>
      </label>
    </RadioGroup>
  </fieldset>
</template>

<script setup>
import { RadioGroup, RadioGroupItem } from './radio-group';
import BcIcon from './BcIcon.vue';

// A choice with a title and a one-line description per option: [{ value, title, description, icon, badge, disabled }]
defineProps({ options: { type: Array, required: true }, legend: { type: String, default: '' }, name: { type: String, default: '' }, columns: { type: Number, default: 0 } });
const model = defineModel({ type: [String, Number, Boolean], default: null });
</script>
