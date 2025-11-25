<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center"
  >
    <div
      class="bg-base-100 p-8 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
    >
      <h2 class="text-2xl font-bold mb-6 flex items-center">
        <font-awesome-icon
          :icon="['fas', 'plus-square']"
          class="mr-3 text-primary"
        />
        {{ $t("modals.createTenant.title") }}
      </h2>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label
            for="name"
            class="block text-sm font-medium text-base-content"
            >{{ $t("modals.createTenant.name") }}</label
          >
          <input
            v-model="formData.name"
            type="text"
            id="name"
            required
            class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label
            for="intro_message"
            class="block text-sm font-medium text-base-content"
            >{{ $t("modals.createTenant.introMessage") }}</label
          >
          <textarea
            v-model="formData.intro_message"
            id="intro_message"
            rows="3"
            class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          ></textarea>
        </div>
        <div>
          <label
            for="system_persona"
            class="block text-sm font-medium text-base-content"
            >{{ $t("modals.createTenant.systemPersona") }}</label
          >
          <textarea
            v-model="formData.system_persona"
            id="system_persona"
            rows="5"
            class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          ></textarea>
        </div>
        <div>
          <label
            for="rag_prompt_template"
            class="block text-sm font-medium text-base-content"
            >{{ $t("modals.createTenant.ragPromptTemplate") }}</label
          >
          <textarea
            v-model="formData.rag_prompt_template"
            id="rag_prompt_template"
            rows="8"
            class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          ></textarea>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              for="doc_language"
              class="block text-sm font-medium text-base-content"
              >{{ $t("modals.createTenant.docLanguage") }}</label
            >
            <select
              v-model="formData.doc_language"
              id="doc_language"
              class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option
                v-for="lang in languageOptions"
                :key="lang.value"
                :value="lang.value"
              >
                {{ lang.text }}
              </option>
            </select>
          </div>
          <div>
            <label
              for="translation_target"
              class="block text-sm font-medium text-base-content"
              >{{ $t("modals.createTenant.translationTarget") }}</label
            >
            <select
              v-model="formData.translation_target"
              id="translation_target"
              class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option
                v-for="lang in languageOptions"
                :key="lang.value"
                :value="lang.value"
              >
                {{ lang.text }}
              </option>
            </select>
          </div>
        </div>
        <div class="flex justify-end space-x-4 pt-4">
          <button
            type="button"
            @click="$emit('close')"
            class="btn btn-secondary"
          >
            <font-awesome-icon :icon="['fas', 'times']" class="mr-2" />
            {{ $t("modals.createTenant.cancel") }}
          </button>
          <button type="submit" class="btn btn-primary">
            <font-awesome-icon :icon="['fas', 'check']" class="mr-2" />
            {{ $t("modals.createTenant.create") }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
  show: Boolean,
});

const emit = defineEmits(["close", "create"]);

const languageOptions = ref([
  { value: "de", text: "German" },
  { value: "en", text: "English" },
  { value: "fr", text: "French" },
]);

const formData = ref({
  name: "",
  intro_message:
    "Hallo! Ich bin dein neuer Chatbot. Ich freue mich riesig darauf, dich zu unterstützen. Was hast du auf dem Herzen?",
  system_persona:
    "Du bist ein warmherziger, enthusiastischer und hilfsbereiter KI-Assistent mit gutem Sinn für Humor.",
  rag_prompt_template:
    "{persona}\n\n{fine_tune_instructions}\n\nBeantworte die folgende Frage basierend auf dem bereitgestellten Kontext.\n\n<context>\n{context}\n</context>\n\nFrage: {input}\n",
  doc_language: "de",
  translation_target: "de",
});

const handleSubmit = () => {
  emit("create", { ...formData.value });
};
</script>
