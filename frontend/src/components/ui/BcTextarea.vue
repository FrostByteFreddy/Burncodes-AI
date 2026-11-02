<template>
  <BcField v-if="label" :label="label" :hint="hint" :error="error" :optional="optional" :html-for="fid">
    <Textarea v-bind="$attrs" :id="fid" v-model="model" :rows="rows" :class="{ 'font-mono text-sm': mono }"
      :aria-invalid="error ? 'true' : undefined" :aria-describedby="error ? `${fid}-err` : hint ? `${fid}-hint` : undefined" />
  </BcField>
  <Textarea v-else v-bind="$attrs" :id="fid" v-model="model" :rows="rows" :class="{ 'font-mono text-sm': mono }" />
</template>

<script setup>
import { Textarea } from './textarea';
import BcField from './BcField.vue';
import { useFieldId } from './useFieldId';

defineOptions({ inheritAttrs: false });
// mono only for real code (the instruction template)
const props = defineProps({
  label: { type: String, default: '' }, hint: { type: String, default: '' }, error: { type: String, default: '' },
  optional: Boolean, mono: Boolean, rows: { type: Number, default: 4 }, id: { type: String, default: '' },
});
const model = defineModel({ type: String, default: '' });
const fid = props.id || useFieldId('ta');
</script>
