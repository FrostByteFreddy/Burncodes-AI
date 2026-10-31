<template>
  <BcField v-if="label" :label="label" :hint="hint" :error="error" :html-for="fid">
    <div :class="['bc-url', state && `is-${state}`]">
      <BcIcon name="globe" class="bc-url__lead" />
      <input v-bind="$attrs" :id="fid" v-model="model" type="url" inputmode="url" autocomplete="url" :placeholder="placeholder"
        class="bc-input bc-url__input" :aria-invalid="state === 'invalid' ? 'true' : undefined"
        :aria-describedby="error ? `${fid}-err` : hint ? `${fid}-hint` : undefined" />
      <span v-if="state === 'checking'" class="bc-spinner bc-spinner--sm bc-url__trail" :aria-label="$t('ui.checking')"></span>
      <BcIcon v-else-if="state === 'valid'" name="circle-check" class="bc-url__trail is-ok" :label="$t('ui.reachable')" />
      <BcIcon v-else-if="state === 'invalid'" name="circle-exclamation" class="bc-url__trail is-err" :label="$t('ui.unreachable')" />
    </div>
  </BcField>
</template>

<script setup>
import BcField from './BcField.vue';
import BcIcon from './BcIcon.vue';
import { useFieldId } from './useFieldId';

defineOptions({ inheritAttrs: false });
// state: checking · valid · invalid
const props = defineProps({
  label: { type: String, required: true }, hint: { type: String, default: '' }, error: { type: String, default: '' },
  state: { type: String, default: '' }, placeholder: { type: String, default: 'www.ihre-gemeinde.ch' }, id: { type: String, default: '' },
});
const model = defineModel({ type: String, default: '' });
const fid = props.id || useFieldId('url');
</script>
