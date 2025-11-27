<template>
  <div class="card">
    <div
      class="inline-flex p-1 space-x-1 bg-primary/10 rounded-full mb-6 w-fit"
    >
      <a
        class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
        :class="{
          '!bg-primary text-primary-content shadow': activeTab === 'behavior',
          'btn-ghost text-base-content': activeTab !== 'behavior',
        }"
        @click="activeTab = 'behavior'"
      >
        <font-awesome-icon :icon="['fas', 'fa-brain']" />
        <span>{{ $t("tenant.settings.tabs.behavior") }}</span>
      </a>
      <a
        class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
        :class="{
          '!bg-primary text-primary-content shadow': activeTab === 'appearance',
          'btn-ghost text-base-content': activeTab !== 'appearance',
        }"
        @click="activeTab = 'appearance'"
      >
        <font-awesome-icon :icon="['fas', 'fa-palette']" />
        <span>{{ $t("tenant.settings.tabs.appearance") }}</span>
      </a>
    </div>

    <form @submit.prevent="handleUpdate" class="space-y-6">
      <div v-show="activeTab === 'behavior'" class="space-y-6">
        <div>
          <label
            for="name"
            class="block text-sm font-medium text-base-content"
            >{{ $t("tenant.settings.behavior.name") }}</label
          >
          <input
            v-model="formData.name"
            type="text"
            id="name"
            required
            class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label
            for="intro_message"
            class="block text-sm font-medium text-base-content"
            >{{ $t("tenant.settings.behavior.introMessage") }}</label
          >
          <AutoGrowTextarea
            v-model="formData.intro_message"
            id="intro_message"
            rows="3"
            class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label
            for="system_persona"
            class="block text-sm font-medium text-base-content"
            >{{ $t("tenant.settings.behavior.systemPersona") }}</label
          >
          <AutoGrowTextarea
            v-model="formData.system_persona"
            id="system_persona"
            rows="5"
            class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label
            for="rag_prompt_template"
            class="block text-sm font-medium text-base-content"
            >{{ $t("tenant.settings.behavior.ragPromptTemplate") }}</label
          >
          <AutoGrowTextarea
            v-model="formData.rag_prompt_template"
            id="rag_prompt_template"
            rows="8"
            class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              for="doc_language"
              class="block text-sm font-medium text-base-content"
              >{{ $t("tenant.settings.behavior.docLanguage") }}</label
            >
            <select
              v-model="formData.doc_language"
              id="doc_language"
              class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
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
              >{{ $t("tenant.settings.behavior.translationTarget") }}</label
            >
            <select
              v-model="formData.translation_target"
              id="translation_target"
              class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
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
      </div>

      <div v-show="activeTab === 'appearance'" @change="handleUpdate">
        <div class="space-y-8">
          <div class="p-6 border border-base-300 rounded-lg bg-base-100">
            <h3 class="text-lg font-bold mb-4 flex items-center">
              <font-awesome-icon
                :icon="['fas', 'code']"
                class="mr-2 text-primary"
              />
              {{ $t("tenant.settings.appearance.installation.title") }}
            </h3>
            <p class="text-sm text-base-content/70 mb-4">
              {{ $t("tenant.settings.appearance.installation.instruction") }}
            </p>
            <div class="relative">
              <pre
                class="bg-base-300 p-4 rounded-lg overflow-x-auto text-sm font-mono text-base-content"
              ><code>&lt;script src="{{ apiUrl }}/tenants/widget.js" data-tenant-id="{{ tenantsStore.currentTenant?.id }}"&gt;&lt;/script&gt;</code></pre>
              <button
                @click.prevent="copyScript"
                class="absolute top-2 right-2 btn btn-sm btn-ghost text-primary hover:bg-base-200"
              >
                <font-awesome-icon :icon="['fas', 'copy']" />
                <span class="ml-1">{{
                  $t("tenant.settings.appearance.installation.copy")
                }}</span>
              </button>
            </div>
          </div>

          <div class="p-4 border border-base-300 rounded-lg">
            <h3 class="text-lg font-bold mb-4">
              {{ $t("tenant.settings.appearance.colorPalette.title") }}
            </h3>
            <p class="text-sm text-base-content/70 mb-4">
              {{ $t("tenant.settings.appearance.colorPalette.description") }}
            </p>
            <div class="space-y-3">
              <div
                v-for="(color, index) in formData.widget_config.color_palette"
                :key="color.id"
                class="flex items-center space-x-3"
              >
                <input
                  v-model="color.value"
                  type="color"
                  class="w-12 h-10 p-1 bg-base-200 border-none rounded-lg cursor-pointer aspect-square"
                />
                <input
                  v-model="color.name"
                  type="text"
                  :placeholder="
                    $t('tenant.settings.appearance.colorPalette.placeholder')
                  "
                  :disabled="index < 2"
                  class="flex-grow p-2 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-base-300/50"
                />
                <button
                  @click.prevent="removeColor(color.id)"
                  v-if="index > 1"
                  class="btn btn-ghost btn-sm text-error"
                >
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
            </div>
            <button
              @click.prevent="addColor"
              class="btn btn-secondary btn-sm mt-4"
            >
              <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
              {{ $t("tenant.settings.appearance.colorPalette.addColor") }}
            </button>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="space-y-8">
              <div class="p-4 border border-base-300 rounded-lg">
                <h3 class="text-lg font-bold mb-4">
                  {{ $t("tenant.settings.appearance.chatWindow.title") }}
                </h3>
                <div class="space-y-4">
                  <div>
                    <label
                      for="chatbot_title"
                      class="block text-sm font-medium"
                      >{{
                        $t("tenant.settings.appearance.chatWindow.chatbotTitle")
                      }}</label
                    >
                    <input
                      v-model="formData.widget_config.chatbot_title"
                      type="text"
                      id="chatbot_title"
                      class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label for="logo" class="block text-sm font-medium">{{
                      $t("tenant.settings.appearance.chatWindow.logo")
                    }}</label>
                    <div class="flex items-center space-x-2 mt-1">
                      <input
                        @change="handleFileUpload($event, 'logo')"
                        type="file"
                        id="logo"
                        class="w-full p-2 bg-base-200 border border-base-300 rounded-lg file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                        accept="image/*,.svg"
                      />
                      <button
                        v-if="formData.widget_config.logo"
                        @click.prevent="removeFile('logo')"
                        class="btn btn-square btn-ghost text-error"
                        :title="
                          $t('tenant.settings.appearance.chatWindow.removeLogo')
                        "
                      >
                        <font-awesome-icon :icon="['fas', 'trash']" />
                      </button>
                    </div>
                    <img
                      v-if="formData.widget_config.logo"
                      :src="formData.widget_config.logo"
                      class="mt-4 max-h-20 rounded-md"
                    />
                  </div>
                  <div class="flex items-center">
                    <input
                      v-model="formData.widget_config.show_reset_button"
                      type="checkbox"
                      id="show_reset_button"
                      class="h-4 w-4 rounded border-base-300 text-primary focus:ring-primary"
                    />
                    <label for="show_reset_button" class="ml-2 block text-sm">{{
                      $t(
                        "tenant.settings.appearance.chatWindow.showResetButton"
                      )
                    }}</label>
                  </div>
                  <div>
                    <label
                      for="input_placeholder"
                      class="block text-sm font-medium"
                      >{{
                        $t(
                          "tenant.settings.appearance.chatWindow.inputPlaceholder"
                        )
                      }}</label
                    >
                    <input
                      v-model="formData.widget_config.input_placeholder"
                      type="text"
                      id="input_placeholder"
                      class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label
                      for="thinking_messages"
                      class="block text-sm font-medium"
                      >{{
                        $t(
                          "tenant.settings.appearance.chatWindow.thinkingMessages"
                        )
                      }}</label
                    >
                    <AutoGrowTextarea
                      v-model="thinkingMessages"
                      id="thinking_messages"
                      class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      rows="3"
                      :placeholder="
                        $t(
                          'tenant.settings.appearance.chatWindow.thinkingPlaceholder'
                        )
                      "
                    />
                  </div>
                </div>
              </div>

              <div class="p-4 border border-base-300 rounded-lg">
                <h3 class="text-lg font-bold mb-4">
                  {{ $t("tenant.settings.appearance.componentStyles.title") }}
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                  <div
                    v-for="(label, key) in filteredComponentStyleLabels"
                    :key="key"
                  >
                    <label :for="key" class="block text-sm font-medium">{{
                      label
                    }}</label>
                    <select
                      v-model="formData.widget_config.component_styles[key]"
                      :id="key"
                      class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option
                        v-for="color in formData.widget_config.color_palette"
                        :key="color.id"
                        :value="color.id"
                      >
                        {{ color.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <div class="p-4 border border-base-300 rounded-lg">
                <h3 class="text-lg font-bold mb-4">
                  {{ $t("tenant.settings.appearance.launcher.title") }}
                </h3>
                <div class="space-y-6">
                  <div>
                    <label
                      for="launcher_icon"
                      class="block text-sm font-medium"
                      >{{
                        $t("tenant.settings.appearance.launcher.icon")
                      }}</label
                    >
                    <div class="flex items-center space-x-2 mt-1">
                      <input
                        @change="handleFileUpload($event, 'launcher_icon')"
                        type="file"
                        id="launcher_icon"
                        class="w-full p-2 bg-base-200 border border-base-300 rounded-lg file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                        accept="image/*,.svg"
                      />
                      <button
                        v-if="formData.widget_config.launcher_icon"
                        @click.prevent="removeFile('launcher_icon')"
                        class="btn btn-square btn-ghost text-error"
                        :title="
                          $t('tenant.settings.appearance.launcher.removeIcon')
                        "
                      >
                        <font-awesome-icon :icon="['fas', 'trash']" />
                      </button>
                    </div>
                    <div
                      v-if="formData.widget_config.launcher_icon"
                      class="mt-2"
                    >
                      <p class="text-xs text-base-content/50 mb-1">
                        {{
                          $t("tenant.settings.appearance.launcher.currentIcon")
                        }}
                      </p>
                      <img
                        :src="formData.widget_config.launcher_icon"
                        class="w-12 h-12 rounded-full object-cover border border-base-300"
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      for="launcher_background_color"
                      class="block text-sm font-medium"
                      >{{
                        $t(
                          "tenant.settings.appearance.launcher.backgroundColor"
                        )
                      }}</label
                    >
                    <select
                      v-model="
                        formData.widget_config.component_styles
                          .launcher_background_color
                      "
                      id="launcher_background_color"
                      class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option
                        v-for="color in formData.widget_config.color_palette"
                        :key="color.id"
                        :value="color.id"
                      >
                        {{ color.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <div class="lg:sticky top-8 space-y-6">
                <div>
                  <h3 class="text-lg font-bold mb-4">
                    {{ $t("tenant.settings.appearance.preview.title") }}
                  </h3>

                  <div>
                    <h4 class="text-sm font-medium text-base-content/70 mb-2">
                      {{ $t("tenant.settings.appearance.preview.chatWindow") }}
                    </h4>
                    <ChatPreview
                      :tenantId="tenantsStore.currentTenant.id"
                      :key="previewKey"
                    />
                  </div>

                  <div class="mb-4">
                    <h4 class="text-sm font-medium text-base-content/70 mb-2">
                      {{ $t("tenant.settings.appearance.preview.launcher") }}
                    </h4>
                    <LauncherPreview
                      :icon="formData.widget_config.launcher_icon"
                      :background-color="
                        getPaletteColor(
                          formData.widget_config.component_styles
                            .launcher_background_color
                        )
                      "
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end mt-8">
        <button
          type="submit"
          :disabled="tenantsStore.loading"
          class="btn btn-primary"
        >
          <span
            v-if="tenantsStore.loading"
            class="flex items-center justify-center"
          >
            <font-awesome-icon
              :icon="['fas', 'spinner']"
              class="w-5 h-5 mr-3 animate-spin"
            />
            {{ $t("tenant.settings.actions.saving") }}
          </span>
          <span v-else class="flex items-center">
            <font-awesome-icon :icon="['fas', 'save']" class="mr-2" />
            {{ $t("tenant.settings.actions.saveChanges") }}
          </span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { useTenantsStore } from "../../stores/tenants";
import { useToast } from "../../composables/useToast";
import AutoGrowTextarea from "../AutoGrowTextarea.vue";
import { v4 as uuidv4 } from "uuid";
import ChatPreview from "./ChatPreview.vue";
import LauncherPreview from "./LauncherPreview.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const activeTab = ref("behavior");
const previewKey = ref(0);

const apiUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

const languageOptions = computed(() => [
  { value: "de", text: "Deutsch" },
  { value: "en", text: "English" },
  { value: "fr", text: "Français" },
]);

const defaultWidgetConfig = () => ({
  chatbot_title: "",
  logo: null,
  launcher_icon: null,
  show_reset_button: true,
  input_placeholder: "Send a message...",
  thinking_messages: [
    "Thinking...",
    "Just a moment...",
    "Let me check that for you...",
  ],
  color_palette: [
    {
      id: "c_white",
      name: t("tenant.settings.defaults.white"),
      value: "#FFFFFF",
    },
    {
      id: "c_black",
      name: t("tenant.settings.defaults.black"),
      value: "#1F2937",
    },
    {
      id: "c_primary",
      name: t("tenant.settings.defaults.primary"),
      value: "#A855F7",
    },
    {
      id: "c_secondary",
      name: t("tenant.settings.defaults.secondary"),
      value: "#F3F4F6",
    },
  ],
  component_styles: {
    header_background_color: "c_secondary",
    header_text_color: "c_black",
    user_message_background_color: "c_primary",
    user_message_text_color: "c_white",
    bot_message_background_color: "c_secondary",
    bot_message_text_color: "c_black",
    send_button_background_color: "c_primary",
    send_button_text_color: "c_white",
    input_background_color: "c_secondary",
    input_text_color: "c_black",
    input_focus_ring_color: "c_primary",
    chat_background_color: "c_white",
    reset_button_color: "c_primary",
    launcher_background_color: "c_primary",
  },
});

const formData = ref({
  name: "",
  intro_message: "",
  system_persona: "",
  rag_prompt_template: "",
  doc_language: "en",
  translation_target: "en",
  widget_config: defaultWidgetConfig(),
});

const componentStyleLabels = computed(() => ({
  header_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.header_background_color"
  ),
  header_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.header_text_color"
  ),
  user_message_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.user_message_background_color"
  ),
  user_message_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.user_message_text_color"
  ),
  bot_message_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.bot_message_background_color"
  ),
  bot_message_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.bot_message_text_color"
  ),
  send_button_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.send_button_background_color"
  ),
  send_button_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.send_button_text_color"
  ),
  input_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.input_background_color"
  ),
  input_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.input_text_color"
  ),
  input_focus_ring_color: t(
    "tenant.settings.appearance.componentStyles.labels.input_focus_ring_color"
  ),
  chat_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.chat_background_color"
  ),
  reset_button_color: t(
    "tenant.settings.appearance.componentStyles.labels.reset_button_color"
  ),
  launcher_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.launcher_background_color"
  ),
}));

const filteredComponentStyleLabels = computed(() => {
  const labels = { ...componentStyleLabels.value };
  delete labels.launcher_background_color;
  return labels;
});

watch(
  () => tenantsStore.currentTenant?.id,
  (newId) => {
    const newTenant = tenantsStore.currentTenant;
    if (newId && newTenant) {
      const newConfig = {
        ...defaultWidgetConfig(),
        ...(newTenant.widget_config || {}),
      };
      newConfig.color_palette =
        newTenant.widget_config?.color_palette ||
        defaultWidgetConfig().color_palette;
      newConfig.component_styles = {
        ...defaultWidgetConfig().component_styles,
        ...(newTenant.widget_config?.component_styles || {}),
      };

      formData.value = {
        name: newTenant.name,
        intro_message: newTenant.intro_message,
        system_persona: newTenant.system_persona,
        rag_prompt_template: newTenant.rag_prompt_template,
        doc_language: newTenant.doc_language,
        translation_target: newTenant.translation_target,
        widget_config: newConfig,
      };
    }
  },
  { immediate: true } // Removed deep: true
);

const thinkingMessages = computed({
  get: () => formData.value.widget_config.thinking_messages.join("\n"),
  set: (value) => {
    formData.value.widget_config.thinking_messages = value
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
  },
});

const addColor = () => {
  formData.value.widget_config.color_palette.push({
    id: uuidv4(),
    name: t("tenant.settings.defaults.newColor"),
    value: "#000000",
  });
};

const removeColor = (idToRemove) => {
  const palette = formData.value.widget_config.color_palette;
  if (palette.length <= 2) {
    addToast(
      t("tenant.settings.appearance.colorPalette.removeBaseColorError"),
      "warning"
    );
    return;
  }
  formData.value.widget_config.color_palette = palette.filter(
    (c) => c.id !== idToRemove
  );
};

// New function to clear images
const removeFile = (field) => {
  formData.value.widget_config[field] = null;
  // Reset the HTML input value so the same file can be selected again if needed
  const inputEl = document.getElementById(field);
  if (inputEl) inputEl.value = "";
  addToast(t("tenant.settings.actions.imageRemoved"), "success");
};

// Encodes a file as a base64 string
const encodeFileAsBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
    reader.readAsDataURL(file);
  });
};

const handleFileUpload = async (event, field) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const base64String = await encodeFileAsBase64(file);
    formData.value.widget_config[field] = base64String;
    addToast(t("tenant.settings.actions.imageUpdated"), "success");
  } catch (error) {
    console.error("File reading error:", error);
    addToast(t("tenant.settings.actions.readFailed"), "error");
  }
};

const handleUpdate = async () => {
  if (tenantsStore.currentTenant && !tenantsStore.loading) {
    try {
      await tenantsStore.updateTenant(
        tenantsStore.currentTenant.id,
        formData.value
      );
      addToast(t("tenant.settings.actions.savedSuccess"), "success");
      previewKey.value++;
    } catch (error) {
      addToast(t("tenant.settings.actions.saveFailed"), "error");
    }
  }
};

const getPaletteColor = (colorId) => {
  const color = formData.value.widget_config.color_palette.find(
    (c) => c.id === colorId
  );
  return color ? color.value : colorId;
};

const copyScript = () => {
  const script = `<script src="${apiUrl}/tenants/widget.js" data-tenant-id="${tenantsStore.currentTenant?.id}"><\/script>`;
  navigator.clipboard
    .writeText(script)
    .then(() => {
      addToast(t("tenant.settings.actions.scriptCopied"), "success");
    })
    .catch(() => {
      addToast(t("tenant.settings.actions.copyFailed"), "error");
    });
};
</script>
