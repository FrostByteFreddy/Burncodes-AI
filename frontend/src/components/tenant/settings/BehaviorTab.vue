<template>
  <div class="space-y-8">
    <div class="settings-section">
      <h3 class="settings-section__title">
        <font-awesome-icon :icon="['fas', 'info-circle']" class="settings-section__icon" />
        General Information
      </h3>
      <div class="space-y-6">
        <div>
          <label for="name" class="form-field">{{ $t("tenant.settings.behavior.name") }}</label>
          <input v-model="local.name" type="text" id="name" required class="form-input" />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label for="doc_language" class="form-field">{{ $t("tenant.settings.behavior.docLanguage") }}</label>
            <select v-model="local.doc_language" id="doc_language" class="form-input">
              <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">{{ lang.text }}</option>
            </select>
          </div>
          <div>
            <label for="translation_target" class="form-field">{{ $t("tenant.settings.behavior.translationTarget") }}</label>
            <select v-model="local.translation_target" id="translation_target" class="form-input">
              <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">{{ lang.text }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-section">
      <h3 class="settings-section__title">
        <font-awesome-icon :icon="['fas', 'user-astronaut']" class="settings-section__icon" />
        AI Persona &amp; Role
      </h3>
      <div class="space-y-6">
        <div>
          <label for="intro_message" class="form-field">{{ $t("tenant.settings.behavior.introMessage") }}</label>
          <AutoGrowTextarea v-model="local.intro_message" id="intro_message" rows="3" class="form-input" />
        </div>
        <div>
          <label for="system_persona" class="form-field">{{ $t("tenant.settings.behavior.systemPersona") }}</label>
          <AutoGrowTextarea v-model="local.system_persona" id="system_persona" rows="4" class="form-input" />
        </div>
      </div>
    </div>

    <div class="settings-section">
      <h3 class="settings-section__title">
        <font-awesome-icon :icon="['fas', 'brain']" class="settings-section__icon" />
        Advanced RAG Configuration
      </h3>
      <div>
        <label for="rag_prompt_template" class="form-field">{{ $t("tenant.settings.behavior.ragPromptTemplate") }}</label>
        <AutoGrowTextarea v-model="local.rag_prompt_template" id="rag_prompt_template" rows="8"
          class="form-input form-input--mono" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import AutoGrowTextarea from '../../AutoGrowTextarea.vue';

const props = defineProps({ modelValue: { type: Object, required: true } });
const emit = defineEmits(['update:modelValue']);

const local = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
});

const languageOptions = [
  { value: 'de', text: 'Deutsch' },
  { value: 'en', text: 'English' },
  { value: 'fr', text: 'Français' },
];
</script>
