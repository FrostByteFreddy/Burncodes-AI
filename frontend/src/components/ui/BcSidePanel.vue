<template>
  <Teleport to="body">
    <div v-if="open" class="bc-overlay bc-overlay--side">
      <div class="bc-scrim" @click="$emit('close')"></div>
      <aside class="bc-sidepanel" role="dialog" aria-modal="true" :aria-label="title">
        <div class="bc-sidepanel__head">
          <div>
            <h2 class="bc-sidepanel__title">{{ title }}</h2>
            <p v-if="subtitle" class="bc-sidepanel__sub">{{ subtitle }}</p>
          </div>
          <BcIconButton icon="xmark" :label="$t('ui.close')" @click="$emit('close')" />
        </div>
        <div v-if="steps" class="bc-sidepanel__steps"><BcStepIndicator :steps="steps" :current="step" /></div>
        <div class="bc-sidepanel__body"><slot /></div>
        <div v-if="$slots.footer" class="bc-sidepanel__foot"><slot name="footer" /></div>
      </aside>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue';
import BcIconButton from './BcIconButton.vue';
import BcStepIndicator from './BcStepIndicator.vue';

const props = defineProps({ open: Boolean, title: { type: String, required: true }, subtitle: { type: String, default: '' }, steps: { type: Array, default: null }, step: { type: Number, default: 0 } });
const emit = defineEmits(['close']);
const onKey = (e) => { if (e.key === 'Escape') emit('close'); };
watch(() => props.open, (o) => (o ? window.addEventListener('keydown', onKey) : window.removeEventListener('keydown', onKey)), { immediate: true });
onBeforeUnmount(() => window.removeEventListener('keydown', onKey));
</script>
