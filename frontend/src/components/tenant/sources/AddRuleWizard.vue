<template>
  <Teleport to="body">
    <Transition name="slide-over">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="handleClose"></div>

        <div class="wizard-panel">

          <!-- Header -->
          <div class="wizard-header">
            <div>
              <h2 class="wizard-title">{{ $t('tenant.fineTune.addRule') }}</h2>
              <div class="wizard-progress">
                <div v-for="i in 2" :key="i"
                  class="wizard-progress__dot"
                  :class="{ 'is-active': i - 1 === step, 'is-done': i - 1 < step }">
                </div>
              </div>
            </div>
            <button @click="handleClose" class="wizard-close">
              <font-awesome-icon :icon="['fas', 'xmark']" />
            </button>
          </div>

          <!-- Step content -->
          <div class="flex-1 overflow-y-auto p-6 space-y-5">

            <!-- Step 0: Trigger -->
            <div v-if="step === 0" class="space-y-5">
              <div class="step-badge">
                <font-awesome-icon :icon="['fas', 'bolt']" />
                {{ $t('tenant.fineTune.wizard.step1of2') }}
              </div>

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

              <!-- Live preview chip -->
              <div v-if="trigger.trim()" class="trigger-preview">
                <span class="trigger-preview__label">{{ $t('tenant.fineTune.wizard.triggerPreview') }}</span>
                <span class="trigger-chip">{{ trigger }}</span>
              </div>
            </div>

            <!-- Step 1: Action -->
            <div v-if="step === 1" class="space-y-5">
              <div class="step-badge step-badge--accent">
                <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" />
                {{ $t('tenant.fineTune.wizard.step2of2') }}
              </div>

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

              <!-- Trigger recap -->
              <div class="recap-card">
                <span class="recap-card__label">{{ $t('tenant.fineTune.trigger.label') }}</span>
                <span class="recap-card__value">{{ trigger }}</span>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="wizard-footer">
            <button v-if="step > 0" @click="step--" class="wiz-btn wiz-btn--ghost">
              <font-awesome-icon :icon="['fas', 'arrow-left']" />
              {{ $t('tenant.fineTune.wizard.back') }}
            </button>
            <button v-if="step < 1" @click="step++" :disabled="!canProceed" class="wiz-btn wiz-btn--primary">
              {{ $t('tenant.fineTune.wizard.next') }}
              <font-awesome-icon :icon="['fas', 'arrow-right']" />
            </button>
            <button v-if="step === 1" @click="submit" :disabled="!canSubmit" class="wiz-btn wiz-btn--primary">
              <font-awesome-icon :icon="['fas', 'check']" />
              {{ $t('tenant.fineTune.actions.add') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({ open: { type: Boolean, default: false } });
const emit = defineEmits(['close', 'add-rule']);

const step        = ref(0);
const trigger     = ref('');
const instruction = ref('');

// Reset when opened
watch(() => props.open, (val) => {
  if (val) { step.value = 0; trigger.value = ''; instruction.value = ''; }
});

const canProceed = computed(() => trigger.value.trim().length > 0);
const canSubmit  = computed(() => trigger.value.trim() && instruction.value.trim());

const handleClose = () => emit('close');

const submit = () => {
  if (!canSubmit.value) return;
  emit('add-rule', {
    trigger:     trigger.value.trim(),
    instruction: instruction.value.trim(),
  });
  emit('close');
};
</script>

<style scoped>
/* ── Slide transition ──────────────────────────────────────────── */
.slide-over-enter-active, .slide-over-leave-active { transition: opacity 0.25s ease; }
.slide-over-enter-active .wizard-panel,
.slide-over-leave-active .wizard-panel { transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); }
.slide-over-enter-from            { opacity: 0; }
.slide-over-enter-from .wizard-panel { transform: translateX(100%); }
.slide-over-leave-to              { opacity: 0; }
.slide-over-leave-to .wizard-panel   { transform: translateX(100%); }

/* ── Panel shell ───────────────────────────────────────────────── */
.wizard-panel {
  position: relative;
  width: 100%;
  max-width: 420px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-1);
  border-left: 1px solid var(--surface-3);
  box-shadow: -8px 0 40px rgba(0,0,0,0.4);
}

/* ── Header ────────────────────────────────────────────────────── */
.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--surface-3);
}
.wizard-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--surface-heading);
}
.wizard-close {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  color: var(--surface-muted);
  cursor: pointer;
  transition: color var(--t-fast), border-color var(--t-fast);
}
.wizard-close:hover { color: var(--surface-text); border-color: var(--surface-muted); }

/* ── Progress dots ─────────────────────────────────────────────── */
.wizard-progress {
  display: flex;
  gap: 6px;
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

/* ── Step badge ────────────────────────────────────────────────── */
.step-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  background: rgba(10,31,171,0.12);
  color: var(--brand-indigo);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.step-badge--accent {
  background: rgba(255,32,149,0.10);
  color: var(--brand-magenta);
}

/* ── Step heading ──────────────────────────────────────────────── */
.step-heading {
  font-size: 18px;
  font-weight: 700;
  color: var(--surface-heading);
  line-height: 1.3;
}

/* ── Info box ──────────────────────────────────────────────────── */
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

/* ── Field ─────────────────────────────────────────────────────── */
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
.field-input--textarea {
  resize: vertical;
  min-height: 110px;
  line-height: 1.5;
}

/* ── Trigger preview ───────────────────────────────────────────── */
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

/* ── Recap card ────────────────────────────────────────────────── */
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

/* ── Footer ────────────────────────────────────────────────────── */
.wizard-footer {
  display: flex;
  gap: 10px;
  padding: 20px 24px;
  border-top: 1px solid var(--surface-3);
}
.wiz-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: opacity var(--t-fast), background var(--t-fast);
}
.wiz-btn--primary { background: var(--gradient-brand); color: white; }
.wiz-btn--primary:hover:not(:disabled) { opacity: 0.9; }
.wiz-btn--primary:disabled { opacity: 0.35; cursor: not-allowed; }
.wiz-btn--ghost { background: var(--surface-2); border: 1px solid var(--surface-3); color: var(--surface-text); }
.wiz-btn--ghost:hover { border-color: var(--surface-muted); }

/* ── Step subtext ──────────────────────────────────────────────── */
.step-subtext { font-size: 13px; color: var(--surface-muted); line-height: 1.5; }

.space-y-5 > * + * { margin-top: 20px; }
</style>
