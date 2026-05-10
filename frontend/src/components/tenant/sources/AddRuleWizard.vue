<template>
  <WizardPanel
    :open="open"
    :title="$t('tenant.fineTune.addRule')"
    :step="step"
    :total-steps="2"
    :can-proceed="canProceed"
    :can-submit="canSubmit"
    :back-label="$t('tenant.fineTune.wizard.back')"
    :next-label="$t('tenant.fineTune.wizard.next')"
    :submit-label="$t('tenant.fineTune.actions.add')"
    @close="handleClose"
    @back="step--"
    @next="step++"
    @submit="submit"
  >
    <!-- Step 0: Trigger -->
    <template v-if="step === 0">
      <div>
        <p class="step-heading">{{ $t('tenant.fineTune.wizard.triggerTitle') }}</p>
      </div>

      <div class="info-box">
        <font-awesome-icon :icon="['fas', 'circle-info']" class="info-box__icon" />
        <p class="step-subtext">{{ $t('tenant.fineTune.wizard.triggerDesc') }}</p>
      </div>

      <div>
        <label for="rule-trigger" class="field-label">{{ $t('tenant.fineTune.trigger.label') }}</label>
        <input
          id="rule-trigger"
          v-model="trigger"
          type="text"
          :placeholder="$t('tenant.fineTune.wizard.triggerExample')"
          class="field-input"
          style="margin-top:8px;"
          @keydown.enter.prevent="canProceed && step++"
        />
      </div>

      <div v-if="trigger.trim()" class="trigger-preview">
        <span class="trigger-preview__label">{{ $t('tenant.fineTune.wizard.triggerPreview') }}</span>
        <span class="trigger-chip">{{ trigger }}</span>
      </div>
    </template>

    <!-- Step 1: Action -->
    <template v-if="step === 1">
      <div>
        <p class="step-heading">{{ $t('tenant.fineTune.wizard.actionTitle') }}</p>
      </div>

      <div class="info-box info-box--accent">
        <font-awesome-icon :icon="['fas', 'circle-info']" class="info-box__icon info-box__icon--accent" />
        <p class="step-subtext">{{ $t('tenant.fineTune.wizard.actionDesc') }}</p>
      </div>

      <div>
        <label for="rule-instruction" class="field-label">{{ $t('tenant.fineTune.instruction.label') }}</label>
        <textarea
          id="rule-instruction"
          v-model="instruction"
          :placeholder="$t('tenant.fineTune.wizard.actionExample')"
          class="field-input field-input--textarea"
          rows="5"
          style="margin-top:8px;"
        ></textarea>
      </div>

      <div class="recap-card">
        <span class="recap-card__label">{{ $t('tenant.fineTune.trigger.label') }}</span>
        <span class="recap-card__value">{{ trigger }}</span>
      </div>
    </template>
  </WizardPanel>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import WizardPanel from '../../WizardPanel.vue';

const props = defineProps({ open: { type: Boolean, default: false } });
const emit = defineEmits(['close', 'add-rule']);

const step        = ref(0);
const trigger     = ref('');
const instruction = ref('');

watch(() => props.open, (val) => {
  if (val) { step.value = 0; trigger.value = ''; instruction.value = ''; }
});

const canProceed = computed(() => trigger.value.trim().length > 0);
const canSubmit  = computed(() => trigger.value.trim() && instruction.value.trim());

const handleClose = () => emit('close');

const submit = () => {
  if (!canSubmit.value) return;
  emit('add-rule', { trigger: trigger.value.trim(), instruction: instruction.value.trim() });
  emit('close');
};
</script>

<style scoped>
.step-heading {
  font-size: 18px;
  font-weight: 700;
  color: var(--surface-heading);
  line-height: 1.3;
}
.step-subtext { font-size: 13px; color: var(--surface-muted); line-height: 1.5; }

.info-box {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
}
.info-box--accent { border-color: rgba(255,32,149,0.2); background: rgba(255,32,149,0.05); }
.info-box__icon { color: var(--brand-indigo); flex-shrink: 0; margin-top: 2px; }
.info-box__icon--accent { color: var(--brand-magenta); }

.field-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--surface-muted);
}
.field-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-text);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
  box-sizing: border-box;
}
.field-input:focus {
  border-color: var(--brand-indigo);
  box-shadow: 0 0 0 3px rgba(10,31,171,0.15);
}
.field-input--textarea { resize: vertical; min-height: 110px; line-height: 1.5; }

.trigger-preview {
  display: flex;
  align-items: center;
  gap: 10px;
}
.trigger-preview__label {
  font-size: 11px;
  font-weight: 600;
  color: var(--surface-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}
.trigger-chip {
  display: inline-block;
  padding: 4px 14px;
  background: rgba(10,31,171,0.12);
  border: 1px solid rgba(10,31,171,0.25);
  color: var(--brand-indigo);
  border-radius: var(--radius-pill);
  font-size: 13px;
  font-weight: 500;
}

.recap-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
}
.recap-card__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--surface-muted);
  flex-shrink: 0;
}
.recap-card__value {
  font-size: 13px;
  color: var(--brand-indigo);
  font-weight: 500;
}
</style>
