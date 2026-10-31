<template>
  <BcField v-if="label" :label="label" :hint="hint" :error="error" :html-for="fid">
    <div class="bc-select">
      <select v-bind="$attrs" :id="fid" v-model="model" class="bc-input">
        <option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
      <BcIcon name="chevron-down" class="bc-select__chev" />
    </div>
  </BcField>
  <div v-else class="bc-select">
    <select v-bind="$attrs" :id="fid" v-model="model" class="bc-input">
      <option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
    </select>
    <BcIcon name="chevron-down" class="bc-select__chev" />
  </div>
</template>

<script setup>
import BcField from './BcField.vue';
import BcIcon from './BcIcon.vue';
import { useFieldId } from './useFieldId';

defineOptions({ inheritAttrs: false });
const props = defineProps({
  options: { type: Array, required: true }, label: { type: String, default: '' }, hint: { type: String, default: '' },
  error: { type: String, default: '' }, id: { type: String, default: '' },
});
const model = defineModel({ type: [String, Number], default: '' });
const fid = props.id || useFieldId('se');
</script>
