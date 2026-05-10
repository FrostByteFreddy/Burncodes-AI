<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex justify-center items-center"
    style="background: rgba(0,0,0,0.65); backdrop-filter: blur(4px);"
  >
    <div class="modal-box">
      <h2 class="modal-box__title">
        <font-awesome-icon :icon="['fas', 'plus-square']" style="margin-right:12px; color:var(--brand-indigo);" />
        {{ $t("modals.createTenant.title") }}
      </h2>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <div class="modal-field">
          <label for="name" class="modal-field__label">{{ $t("modals.createTenant.name") }}</label>
          <input v-model="formData.name" type="text" id="name" required class="modal-field__input" />
        </div>

        <div class="modal-field">
          <label for="intro_message" class="modal-field__label">{{ $t("modals.createTenant.introMessage") }}</label>
          <textarea v-model="formData.intro_message" id="intro_message" rows="3" class="modal-field__input" />
        </div>

        <div class="modal-field">
          <label for="system_persona" class="modal-field__label">{{ $t("modals.createTenant.systemPersona") }}</label>
          <textarea v-model="formData.system_persona" id="system_persona" rows="4" class="modal-field__input" />
        </div>

        <div class="modal-field">
          <label for="rag_prompt_template" class="modal-field__label">{{ $t("modals.createTenant.ragPromptTemplate") }}</label>
          <textarea v-model="formData.rag_prompt_template" id="rag_prompt_template" rows="6" class="modal-field__input" />
        </div>

        <div class="modal-grid-2">
          <div class="modal-field">
            <label for="doc_language" class="modal-field__label">{{ $t("modals.createTenant.docLanguage") }}</label>
            <select v-model="formData.doc_language" id="doc_language" class="modal-field__input modal-field__select">
              <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">{{ lang.text }}</option>
            </select>
          </div>
          <div class="modal-field">
            <label for="translation_target" class="modal-field__label">{{ $t("modals.createTenant.translationTarget") }}</label>
            <select v-model="formData.translation_target" id="translation_target" class="modal-field__input modal-field__select">
              <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">{{ lang.text }}</option>
            </select>
          </div>
        </div>

        <div class="modal-box__footer">
          <p v-if="error" class="modal-error">{{ error }}</p>
          <button type="button" @click="$emit('close')" class="modal-btn modal-btn--ghost" :disabled="submitting">
            <font-awesome-icon :icon="['fas', 'times']" />
            {{ $t("modals.createTenant.cancel") }}
          </button>
          <button type="submit" class="modal-btn modal-btn--primary" :disabled="submitting">
            <font-awesome-icon :icon="['fas', submitting ? 'spinner' : 'check']" :spin="submitting" />
            {{ submitting ? 'Creating…' : $t("modals.createTenant.create") }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useTenantsStore } from "../stores/tenants";
import { useRouter } from "vue-router";

defineProps({ show: Boolean });
const emit = defineEmits(["close"]);

const tenantsStore = useTenantsStore();
const router = useRouter();

const submitting = ref(false);
const error      = ref("");

const languageOptions = ref([
  { value: "de", text: "German" },
  { value: "en", text: "English" },
  { value: "fr", text: "French" },
]);

const formData = ref({
  name: "",
  intro_message: "Hallo! Ich bin dein neuer Chatbot. Ich freue mich riesig darauf, dich zu unterstützen. Was hast du auf dem Herzen?",
  system_persona: "Du bist ein warmherziger, enthusiastischer und hilfsbereiter KI-Assistent mit gutem Sinn für Humor.",
  rag_prompt_template: "{persona}\n\n{fine_tune_instructions}\n\nBeantworte die folgende Frage basierend auf dem bereitgestellten Kontext.\n\n<context>\n{context}\n</context>\n\nFrage: {input}\n",
  doc_language: "de",
  translation_target: "de",
});

const handleSubmit = async () => {
  error.value = "";
  submitting.value = true;
  try {
    const newTenant = await tenantsStore.createTenant({ ...formData.value });
    emit("close");
    // Navigate to the new tenant's dashboard
    if (newTenant?.id) {
      router.push(`/tenant/${newTenant.id}`);
    }
  } catch (e) {
    error.value = tenantsStore.error || "Failed to create chatbot.";
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.modal-box {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 32px;
  width: 100%; max-width: 640px;
  max-height: 90vh; overflow-y: auto;
  margin: 16px;
}
.modal-box__title {
  display: flex; align-items: center;
  font-size: 20px; font-weight: 700;
  color: var(--surface-heading);
  margin-bottom: 28px;
}
.modal-form { display: flex; flex-direction: column; gap: 20px; }
.modal-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.modal-field { display: flex; flex-direction: column; gap: 8px; }
.modal-field__label {
  font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--surface-muted);
}
.modal-field__input {
  width: 100%; padding: 10px 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-text); font-size: 14px;
  outline: none;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
  resize: vertical;
}
.modal-field__input:focus {
  border-color: var(--brand-indigo);
  box-shadow: 0 0 0 3px rgba(10,31,171,0.15);
}
.modal-field__select { appearance: none; cursor: pointer; }
.modal-box__footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding-top: 24px; border-top: 1px solid var(--surface-3);
}
.modal-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 20px; font-size: 13px; font-weight: 600;
  border: none; border-radius: var(--radius-md);
  cursor: pointer; transition: opacity var(--t-fast);
}
.modal-btn--ghost { background: var(--surface-2); color: var(--surface-muted); }
.modal-btn--ghost:hover { background: var(--surface-3); color: var(--surface-text); }
.modal-btn--primary { background: var(--gradient-brand); color: white; }
.modal-btn--primary:hover { opacity: 0.9; }
.modal-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.modal-error {
  flex: 1;
  font-size: 13px;
  color: var(--color-error, #f87171);
  margin: 0;
}
</style>
