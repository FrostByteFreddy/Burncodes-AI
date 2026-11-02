<template>
  <Sheet :open="open" @update:open="(o) => { if (!o) $emit('close'); }">
    <SheetContent side="right" :show-close-button="false" class="w-[min(var(--sidepanel-width),100vw)]! max-w-none! gap-0 text-base">
      <div class="bc-sidepanel__head">
        <div>
          <SheetTitle class="bc-sidepanel__title">{{ title }}</SheetTitle>
          <SheetDescription v-if="subtitle" class="bc-sidepanel__sub">{{ subtitle }}</SheetDescription>
        </div>
        <BcIconButton icon="xmark" :label="$t('ui.close')" @click="$emit('close')" />
      </div>
      <div v-if="steps" class="bc-sidepanel__steps"><BcStepIndicator :steps="steps" :current="step" /></div>
      <div class="bc-sidepanel__body"><slot /></div>
      <div v-if="$slots.footer" class="bc-sidepanel__foot"><slot name="footer" /></div>
    </SheetContent>
  </Sheet>
</template>

<script setup>
import { Sheet, SheetContent, SheetDescription, SheetTitle } from './sheet';
import BcIconButton from './BcIconButton.vue';
import BcStepIndicator from './BcStepIndicator.vue';

defineProps({ open: Boolean, title: { type: String, required: true }, subtitle: { type: String, default: '' }, steps: { type: Array, default: null }, step: { type: Number, default: 0 } });
defineEmits(['close']);
</script>
