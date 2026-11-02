<template>
  <Sheet :open="open" @update:open="(o) => { if (!o) $emit('close'); }">
    <SheetContent side="right" :show-close-button="false" class="w-[min(420px,100vw)]! max-w-none! gap-0 text-base">
      <!-- Header -->
      <div class="wizard-header">
        <div>
          <SheetTitle class="wizard-title">{{ title }}</SheetTitle>
          <div class="wizard-progress">
            <div
              v-for="i in totalSteps" :key="i"
              class="wizard-progress__dot"
              :class="{ 'is-active': i - 1 === step, 'is-done': i - 1 < step }"
            ></div>
          </div>
        </div>
        <BcIconButton icon="xmark" :label="$t('ui.close')" @click="$emit('close')" />
      </div>

      <!-- Step content -->
      <div class="wizard-body">
        <slot />
      </div>

      <!-- Footer -->
      <div class="wizard-footer">
        <BcButton v-if="step > 0" variant="quiet" icon="arrow-left" @click="$emit('back')">{{ backLabel }}</BcButton>
        <BcButton v-if="step < totalSteps - 1" variant="primary" icon-right="arrow-right" class="flex-1" :disabled="!canProceed" @click="$emit('next')">{{ nextLabel }}</BcButton>
        <BcButton v-if="step === totalSteps - 1" variant="primary" class="flex-1" :disabled="!canSubmit" :loading="submitting" @click="$emit('submit')">{{ submitLabel }}</BcButton>
      </div>
    </SheetContent>
  </Sheet>
</template>

<script setup>
import { Sheet, SheetContent, SheetTitle } from './ui/sheet';
import { BcButton, BcIconButton } from './ui';

defineProps({
  open:        { type: Boolean, default: false },
  title:       { type: String,  required: true },
  step:        { type: Number,  default: 0 },
  totalSteps:  { type: Number,  required: true },
  canProceed:  { type: Boolean, default: true },
  canSubmit:   { type: Boolean, default: true },
  submitting:  { type: Boolean, default: false },
  backLabel:   { type: String,  default: 'Back' },
  nextLabel:   { type: String,  default: 'Next' },
  submitLabel: { type: String,  default: 'Submit' },
});
defineEmits(['close', 'back', 'next', 'submit']);
</script>

<style scoped>
/* ── Slide transition ──────────────────────────────────────────── */
/* ── Panel shell ───────────────────────────────────────────────── */
/* ── Header ────────────────────────────────────────────────────── */
.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--surface-3);
  flex-shrink: 0;
}
.wizard-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--surface-heading);
}
/* ── Progress dots ─────────────────────────────────────────────── */
.wizard-progress {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.wizard-progress__dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--surface-3);
  transition: background var(--t-fast), transform var(--t-fast);
}
.wizard-progress__dot.is-active { background: var(--brand-indigo); transform: scale(1.3); }
.wizard-progress__dot.is-done   { background: var(--status-success); }

/* ── Body (scrollable) ─────────────────────────────────────────── */
.wizard-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Footer ────────────────────────────────────────────────────── */
.wizard-footer {
  display: flex;
  gap: 8px;
  padding: 20px 24px;
  border-top: 1px solid var(--surface-3);
  flex-shrink: 0;
}
</style>
