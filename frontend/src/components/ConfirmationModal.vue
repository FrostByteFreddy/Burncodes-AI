<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center"
    style="background: rgba(0,0,0,0.65); backdrop-filter: blur(4px);"
  >
    <div class="modal-box">
      <h2 class="modal-box__title">
        <font-awesome-icon
          :icon="['fas', 'triangle-exclamation']"
          style="margin-right: 12px; color: var(--status-error);"
        />
        {{ title }}
      </h2>
      <p class="modal-box__body" v-html="message"></p>

      <div v-if="confirmationText" style="margin-bottom: 24px;">
        <label class="modal-box__label">
          {{ $t("modals.confirmation.typeToConfirm", { text: confirmationText }) }}
        </label>
        <input
          v-model="userInput"
          type="text"
          class="modal-box__input"
        />
      </div>

      <div class="modal-box__footer">
        <button @click="onCancel" class="modal-btn modal-btn--ghost">
          <font-awesome-icon :icon="['fas', 'times']" />
          {{ $t("modals.confirmation.cancel") }}
        </button>
        <button
          @click="onConfirm"
          :disabled="isConfirmDisabled"
          class="modal-btn modal-btn--danger"
        >
          <font-awesome-icon :icon="['fas', 'check']" />
          {{ confirmButtonText || $t("modals.confirmation.confirm") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from "vue";

const props = defineProps({
  show: Boolean,
  title: { type: String, required: true },
  message: { type: String, required: true },
  confirmationText: { type: String, default: "" },
  confirmButtonText: { type: String, default: "" },
});

const emit = defineEmits(["confirm", "cancel"]);
const userInput = ref("");

const isConfirmDisabled = computed(() => {
  if (!props.confirmationText) return false;
  return userInput.value !== props.confirmationText;
});

const onConfirm = () => { if (!isConfirmDisabled.value) emit("confirm"); };
const onCancel  = () => emit("cancel");
</script>

<style scoped>
.modal-box {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 32px;
  width: 100%; max-width: 440px;
  margin: 16px;
}
.modal-box__title {
  display: flex; align-items: center;
  font-size: 20px; font-weight: 700;
  color: var(--surface-heading);
  margin-bottom: 16px;
}
.modal-box__body {
  font-size: 14px; color: var(--surface-muted);
  line-height: 1.6; margin-bottom: 24px;
}
.modal-box__label {
  display: block; font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--surface-muted); margin-bottom: 8px;
}
.modal-box__input {
  width: 100%; padding: 10px 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-text); font-size: 14px;
  outline: none;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.modal-box__input:focus {
  border-color: var(--brand-indigo);
  box-shadow: 0 0 0 3px rgba(10,31,171,0.15);
}
.modal-box__footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding-top: 24px; border-top: 1px solid var(--surface-3);
}
.modal-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 20px; font-size: 13px; font-weight: 600;
  border: none; border-radius: var(--radius-md);
  cursor: pointer; transition: opacity var(--t-fast), background var(--t-fast);
}
.modal-btn--ghost {
  background: var(--surface-2); color: var(--surface-muted);
}
.modal-btn--ghost:hover { background: var(--surface-3); color: var(--surface-text); }
.modal-btn--danger {
  background: var(--status-error); color: white;
}
.modal-btn--danger:hover:not(:disabled) { opacity: 0.88; }
.modal-btn--danger:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
