<template>
  <div>
    <p class="form-field">{{ label }}</p>
    <div class="imgf">
      <div class="imgf__preview">
        <img v-if="modelValue" :src="modelValue" alt="" />
        <font-awesome-icon v-else :icon="['fas', 'image']" class="imgf__empty" />
      </div>
      <div class="imgf__actions">
        <Button as-child variant="outline"><label class="imgf__upload">
          <font-awesome-icon :icon="['fas', 'upload']" />
          {{ modelValue ? $t('configure.image.replace') : $t('configure.image.choose') }}
          <input :id="field" type="file" accept="image/*,.svg" class="imgf__file" @change="onFile" />
        </label></Button>
        <BcButton variant="secondary" v-if="modelValue" type="button"  @click="$emit('update:modelValue', null)">
          {{ $t('configure.image.remove') }}
        </BcButton>
      </div>
    </div>
    <p v-if="hint" class="field-hint">{{ hint }}</p>
  </div>
</template>

<script setup>
import { BcButton } from '@/components/ui';
import { Button } from '@/components/ui/button';
import { useI18n } from 'vue-i18n';
import { useToast } from '@/composables/useToast';

defineProps({
  modelValue: { type: String, default: null },
  field:      { type: String, required: true },
  label:      { type: String, required: true },
  hint:       { type: String, default: '' },
});
const emit = defineEmits(['update:modelValue']);
const { t } = useI18n();
const { addToast } = useToast();

const onFile = (event) => {
  const file = event.target.files[0];
  event.target.value = '';
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => emit('update:modelValue', reader.result);
  reader.onerror = () => addToast(t('tenant.settings.actions.readFailed'), 'error');
  reader.readAsDataURL(file);
};
</script>

<style scoped>
.imgf { display: flex; align-items: center; gap: 16px; margin-top: 8px; }
.imgf__preview {
  width: 64px; height: 64px; flex-shrink: 0; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center; overflow: hidden;
  background: var(--surface-2); border: 1px solid var(--surface-3);
}
.imgf__preview img { max-width: 100%; max-height: 100%; object-fit: contain; }
.imgf__empty { color: var(--surface-muted); font-size: 20px; }
.imgf__actions { display: flex; gap: 8px; flex-wrap: wrap; }
.imgf__upload { position: relative; cursor: pointer; }
.imgf__upload:focus-within { box-shadow: var(--focus-ring-shadow); }
.imgf__file { position: absolute; width: 1px; height: 1px; opacity: 0; }
</style>
