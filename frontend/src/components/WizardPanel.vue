<template>
  <Teleport to="body">
    <Transition name="slide-over">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')"></div>

        <div class="wizard-panel">

          <!-- Header -->
          <div class="wizard-header">
            <div>
              <h2 class="wizard-title">{{ title }}</h2>
              <div class="wizard-progress">
                <div
                  v-for="i in totalSteps" :key="i"
                  class="wizard-progress__dot"
                  :class="{ 'is-active': i - 1 === step, 'is-done': i - 1 < step }"
                ></div>
              </div>
            </div>
            <button @click="$emit('close')" class="wizard-close">
              <font-awesome-icon :icon="['fas', 'xmark']" />
            </button>
          </div>

          <!-- Step content -->
          <div class="wizard-body">
            <slot />
          </div>

          <!-- Footer -->
          <div class="wizard-footer">
            <button v-if="step > 0" @click="$emit('back')" class="wiz-btn wiz-btn--ghost">
              <font-awesome-icon :icon="['fas', 'arrow-left']" />
              {{ backLabel }}
            </button>
            <button
              v-if="step < totalSteps - 1"
              @click="$emit('next')"
              :disabled="!canProceed"
              class="wiz-btn wiz-btn--primary"
            >
              {{ nextLabel }}
              <font-awesome-icon :icon="['fas', 'arrow-right']" />
            </button>
            <button
              v-if="step === totalSteps - 1"
              @click="$emit('submit')"
              :disabled="!canSubmit || submitting"
              class="wiz-btn wiz-btn--primary"
            >
              <font-awesome-icon v-if="submitting" :icon="['fas', 'spinner']" class="spin" />
              {{ submitLabel }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
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
.slide-over-enter-active, .slide-over-leave-active { transition: opacity 0.25s ease; }
.slide-over-enter-active .wizard-panel,
.slide-over-leave-active .wizard-panel { transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); }
.slide-over-enter-from              { opacity: 0; }
.slide-over-enter-from .wizard-panel { transform: translateX(100%); }
.slide-over-leave-to                { opacity: 0; }
.slide-over-leave-to .wizard-panel  { transform: translateX(100%); }

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
  flex-shrink: 0;
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
  gap: 10px;
  padding: 20px 24px;
  border-top: 1px solid var(--surface-3);
  flex-shrink: 0;
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

.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
