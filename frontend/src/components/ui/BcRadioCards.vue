<template>
  <fieldset :class="['bc-radiocards', { 'bc-radiocards--stack': columns === 1 }]">
    <legend v-if="legend" class="bc-field__label">{{ legend }}</legend>
    <div class="bc-radiocards__grid">
      <label v-for="o in options" :key="o.value" :class="['bc-radiocard', { 'is-checked': model === o.value, 'is-disabled': o.disabled }]">
        <input type="radio" class="bc-radiocard__input" :name="groupName" :value="o.value" :checked="model === o.value" :disabled="o.disabled" @change="model = o.value" />
        <span class="bc-radiocard__radio" aria-hidden="true"></span>
        <span v-if="o.icon" class="bc-radiocard__icon"><BcIcon :name="o.icon" /></span>
        <span class="bc-radiocard__text">
          <span class="bc-radiocard__title">{{ o.title }}<span v-if="o.badge" class="bc-radiocard__badge">{{ o.badge }}</span></span>
          <span v-if="o.description" class="bc-radiocard__desc">{{ o.description }}</span>
        </span>
      </label>
    </div>
  </fieldset>
</template>

<script setup>
import BcIcon from './BcIcon.vue';
import { useFieldId } from './useFieldId';

// A choice with a title and a one-line description per option: [{ value, title, description, icon, badge, disabled }]
const props = defineProps({ options: { type: Array, required: true }, legend: { type: String, default: '' }, name: { type: String, default: '' }, columns: { type: Number, default: 0 } });
const model = defineModel({ type: [String, Number, Boolean], default: null });
const groupName = props.name || useFieldId('rc');
</script>
