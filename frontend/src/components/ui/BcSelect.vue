<template>
  <BcField v-if="label" :label="label" :hint="hint" :error="error" :html-for="fid">
    <NativeSelect v-bind="$attrs" :id="fid" v-model="model">
      <NativeSelectOption v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</NativeSelectOption>
    </NativeSelect>
  </BcField>
  <NativeSelect v-else v-bind="$attrs" :id="fid" v-model="model">
    <NativeSelectOption v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</NativeSelectOption>
  </NativeSelect>
</template>

<script setup>
import { NativeSelect, NativeSelectOption } from './native-select';
import BcField from './BcField.vue';
import { useFieldId } from './useFieldId';

defineOptions({ inheritAttrs: false });
const props = defineProps({
  options: { type: Array, required: true }, label: { type: String, default: '' }, hint: { type: String, default: '' },
  error: { type: String, default: '' }, id: { type: String, default: '' },
});
const model = defineModel({ type: [String, Number], default: '' });
const fid = props.id || useFieldId('se');
</script>
