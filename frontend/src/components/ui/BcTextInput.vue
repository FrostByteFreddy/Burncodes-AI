<template>
  <BcField v-if="label" :label="label" :hint="hint" :error="error" :optional="optional" :html-for="fid">
    <input v-bind="$attrs" :id="fid" v-model="model" :type="type" class="bc-input" :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? `${fid}-err` : hint ? `${fid}-hint` : undefined" />
  </BcField>
  <input v-else v-bind="$attrs" :id="fid" v-model="model" :type="type" class="bc-input" :aria-invalid="error ? 'true' : undefined" />
</template>

<script setup>
import BcField from './BcField.vue';
import { useFieldId } from './useFieldId';

defineOptions({ inheritAttrs: false });
const props = defineProps({
  label: { type: String, default: '' }, hint: { type: String, default: '' }, error: { type: String, default: '' },
  optional: Boolean, id: { type: String, default: '' }, type: { type: String, default: 'text' },
});
const model = defineModel({ type: [String, Number], default: '' });
const fid = props.id || useFieldId('in');
</script>
