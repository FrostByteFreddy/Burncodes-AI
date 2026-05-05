<template>
  <div class="space-y-8">
    <!-- General Information -->
    <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
      <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
        <font-awesome-icon :icon="['fas', 'info-circle']" class="mr-3 text-primary" />
        General Information
      </h3>
      <div class="space-y-6">
        <div>
          <label for="name" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.behavior.name") }}</label>
          <input v-model="local.name" type="text" id="name" required
            class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow" />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label for="doc_language" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.behavior.docLanguage") }}</label>
            <select v-model="local.doc_language" id="doc_language"
              class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow">
              <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">{{ lang.text }}</option>
            </select>
          </div>
          <div>
            <label for="translation_target" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.behavior.translationTarget") }}</label>
            <select v-model="local.translation_target" id="translation_target"
              class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow">
              <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">{{ lang.text }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Persona & Role -->
    <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
      <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
        <font-awesome-icon :icon="['fas', 'user-astronaut']" class="mr-3 text-primary" />
        AI Persona &amp; Role
      </h3>
      <div class="space-y-6">
        <div>
          <label for="intro_message" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.behavior.introMessage") }}</label>
          <AutoGrowTextarea v-model="local.intro_message" id="intro_message" rows="3"
            class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none" />
        </div>
        <div>
          <label for="system_persona" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.behavior.systemPersona") }}</label>
          <AutoGrowTextarea v-model="local.system_persona" id="system_persona" rows="4"
            class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none" />
        </div>
      </div>
    </div>

    <!-- Advanced RAG -->
    <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
      <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
        <font-awesome-icon :icon="['fas', 'brain']" class="mr-3 text-primary" />
        Advanced RAG Configuration
      </h3>
      <div>
        <label for="rag_prompt_template" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.behavior.ragPromptTemplate") }}</label>
        <AutoGrowTextarea v-model="local.rag_prompt_template" id="rag_prompt_template" rows="8"
          class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow font-mono text-sm resize-none" />
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
