<template>
  <div class="space-y-8">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left column -->
      <div class="space-y-8">
        <!-- Color Palette -->
        <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
          <h3 class="text-xl font-bold text-base-content mb-4 flex items-center">
            <font-awesome-icon :icon="['fas', 'palette']" class="mr-3 text-primary" />
            {{ $t('tenant.settings.appearance.colorPalette.title') }}
          </h3>
          <p class="text-sm text-base-content/70 mb-4">{{ $t('tenant.settings.appearance.colorPalette.description') }}</p>
          <div class="flex flex-wrap gap-3">
            <div v-for="(color, index) in local.widget_config.color_palette" :key="color.id"
              class="relative group flex flex-col items-center gap-1.5">
              <label class="relative cursor-pointer block">
                <span class="block w-12 h-12 rounded-xl shadow-sm ring-1 ring-black/10 transition-transform group-hover:scale-105"
                  :style="{ backgroundColor: color.value }" />
                <input v-model="color.value" type="color" class="absolute inset-0 opacity-0 w-full h-full cursor-pointer" />
                <button v-if="index > 1" type="button" @click.prevent.stop="removeColor(color.id)"
                  class="absolute -top-1.5 -right-1.5 w-4 h-4 bg-error text-white rounded-full hidden group-hover:flex items-center justify-center leading-none"
                  style="font-size:10px;">×</button>
              </label>
              <input v-model="color.name" type="text" :disabled="index < 2"
                class="w-12 text-xs text-center bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-primary/50 rounded p-0 disabled:cursor-default" />
            </div>
            <div class="flex flex-col items-center gap-1.5">
              <button type="button" @click.prevent="addColor"
                class="w-12 h-12 rounded-xl border-2 border-dashed border-base-300 flex items-center justify-center text-base-content/30 hover:border-primary/50 hover:text-primary/50 transition-colors">
                <font-awesome-icon :icon="['fas', 'plus']" />
              </button>
              <span class="w-12 text-xs text-center text-base-content/30">Add</span>
            </div>
          </div>
        </div>

        <!-- Chat Window -->
        <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
          <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
            <font-awesome-icon :icon="['fas', 'comment-dots']" class="mr-3 text-primary" />
            {{ $t("tenant.settings.appearance.chatWindow.title") }}
          </h3>
          <div class="space-y-4">
            <div>
              <label for="chatbot_title" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.appearance.chatWindow.chatbotTitle") }}</label>
              <input v-model="local.widget_config.chatbot_title" type="text" id="chatbot_title"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow" />
            </div>
            <div>
              <label for="logo" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.appearance.chatWindow.logo") }}</label>
              <div class="flex items-center space-x-2 mt-1">
                <input @change="handleFileUpload($event, 'logo')" type="file" id="logo" accept="image/*,.svg"
                  class="w-full p-2 bg-base-200 border-none rounded-xl file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20" />
                <button v-if="local.widget_config.logo" @click.prevent="removeFile('logo')"
                  class="btn btn-square btn-ghost text-error hover:bg-error/10">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
              <img v-if="local.widget_config.logo" :src="local.widget_config.logo" class="mt-4 max-h-20 rounded-lg shadow-sm" />
            </div>
            <div class="flex items-center">
              <input v-model="local.widget_config.show_reset_button" type="checkbox" id="show_reset_button"
                class="h-4 w-4 rounded border-base-200 text-primary focus:ring-primary/50 bg-base-200" />
              <label for="show_reset_button" class="ml-2 block text-sm text-base-content">{{ $t("tenant.settings.appearance.chatWindow.showResetButton") }}</label>
            </div>
            <div>
              <label for="input_placeholder" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.appearance.chatWindow.inputPlaceholder") }}</label>
              <input v-model="local.widget_config.input_placeholder" type="text" id="input_placeholder"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow" />
            </div>
            <div>
              <label for="thinking_messages" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.appearance.chatWindow.thinkingMessages") }}</label>
              <AutoGrowTextarea v-model="thinkingMessages" id="thinking_messages" rows="3"
                :placeholder="$t('tenant.settings.appearance.chatWindow.thinkingPlaceholder')"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none" />
            </div>
          </div>
        </div>

        <!-- Component Styles -->
        <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
          <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
            <font-awesome-icon :icon="['fas', 'swatchbook']" class="mr-3 text-primary" />
            {{ $t("tenant.settings.appearance.componentStyles.title") }}
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div v-for="(label, key) in filteredComponentStyleLabels" :key="key">
              <label :for="key" class="block text-sm font-medium text-base-content">{{ label }}</label>
              <select v-model="local.widget_config.component_styles[key]" :id="key"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow">
                <option v-for="color in local.widget_config.color_palette" :key="color.id" :value="color.id">{{ color.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Launcher -->
        <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
          <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
            <font-awesome-icon :icon="['fas', 'rocket']" class="mr-3 text-primary" />
            {{ $t("tenant.settings.appearance.launcher.title") }}
          </h3>
          <div class="space-y-6">
            <div>
              <label for="launcher_icon" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.appearance.launcher.icon") }}</label>
              <div class="flex items-center space-x-2 mt-1">
                <input @change="handleFileUpload($event, 'launcher_icon')" type="file" id="launcher_icon" accept="image/*,.svg"
                  class="w-full p-2 bg-base-200 border-none rounded-xl file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20" />
                <button v-if="local.widget_config.launcher_icon" @click.prevent="removeFile('launcher_icon')"
                  class="btn btn-square btn-ghost text-error hover:bg-error/10">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
              <div v-if="local.widget_config.launcher_icon" class="mt-4">
                <p class="text-xs text-base-content/50 mb-2">{{ $t("tenant.settings.appearance.launcher.currentIcon") }}</p>
                <img :src="local.widget_config.launcher_icon" class="w-12 h-12 rounded-full object-cover shadow-sm bg-base-200 p-1" />
              </div>
            </div>
            <div>
              <label for="launcher_background_color" class="block text-sm font-medium text-base-content">{{ $t("tenant.settings.appearance.launcher.backgroundColor") }}</label>
              <select v-model="local.widget_config.component_styles.launcher_background_color" id="launcher_background_color"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow">
                <option v-for="color in local.widget_config.color_palette" :key="color.id" :value="color.id">{{ color.name }}</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Right column — sticky preview -->
      <div>
        <div class="lg:sticky top-8 space-y-6">
          <ChatPreview :tenantId="tenantId" :key="previewKey" />
          <div class="mb-4">
            <h4 class="text-sm font-medium text-base-content/70 mb-2">{{ $t("tenant.settings.appearance.preview.launcher") }}</h4>
            <LauncherPreview :icon="local.widget_config.launcher_icon" :background-color="getPaletteColor(local.widget_config.component_styles.launcher_background_color)" />
          </div>
        </div>
      </div>
    </div>

    <!-- Installation Script -->
    <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm mt-2">
      <h3 class="text-xl font-bold text-base-content mb-4 flex items-center">
        <font-awesome-icon :icon="['fas', 'code']" class="mr-3 text-primary" />
        {{ $t('tenant.settings.appearance.installation.title') }}
      </h3>
      <p class="text-sm text-base-content/70 mb-4">{{ $t('tenant.settings.appearance.installation.instruction') }}</p>
      <div class="relative">
        <pre class="bg-base-200/50 p-4 rounded-lg overflow-x-auto text-sm font-mono text-base-content border border-base-200"><code>&lt;script src="{{ apiUrl }}/tenants/widget.js" data-tenant-id="{{ tenantId }}"&gt;&lt;/script&gt;</code></pre>
        <button @click.prevent="copyScript" class="absolute top-2 right-2 btn btn-sm btn-ghost text-primary hover:bg-base-300">
          <font-awesome-icon :icon="['fas', 'copy']" />
          <span class="ml-1">{{ $t('tenant.settings.appearance.installation.copy') }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useToast } from '../../../composables/useToast';
import { v4 as uuidv4 } from 'uuid';
import AutoGrowTextarea from '../../AutoGrowTextarea.vue';
import ChatPreview from '../ChatPreview.vue';
import LauncherPreview from '../LauncherPreview.vue';

const props = defineProps({
  modelValue: { type: Object, required: true },
  tenantId: { type: String, required: true },
  previewKey: { type: Number, default: 0 },
  apiUrl: { type: String, default: '' },
});
const emit = defineEmits(['update:modelValue']);
const { t } = useI18n();
const { addToast } = useToast();

const local = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
});

const thinkingMessages = computed({
  get: () => local.value.widget_config.thinking_messages.join('\n'),
  set: (v) => { local.value.widget_config.thinking_messages = v.split('\n').map(s => s.trim()).filter(Boolean); },
});

const styleKeyLabels = computed(() => ({
  header_background_color: t('tenant.settings.appearance.componentStyles.labels.header_background_color'),
  header_text_color: t('tenant.settings.appearance.componentStyles.labels.header_text_color'),
  user_message_background_color: t('tenant.settings.appearance.componentStyles.labels.user_message_background_color'),
  user_message_text_color: t('tenant.settings.appearance.componentStyles.labels.user_message_text_color'),
  bot_message_background_color: t('tenant.settings.appearance.componentStyles.labels.bot_message_background_color'),
  bot_message_text_color: t('tenant.settings.appearance.componentStyles.labels.bot_message_text_color'),
  send_button_background_color: t('tenant.settings.appearance.componentStyles.labels.send_button_background_color'),
  send_button_text_color: t('tenant.settings.appearance.componentStyles.labels.send_button_text_color'),
  input_background_color: t('tenant.settings.appearance.componentStyles.labels.input_background_color'),
  input_text_color: t('tenant.settings.appearance.componentStyles.labels.input_text_color'),
  input_focus_ring_color: t('tenant.settings.appearance.componentStyles.labels.input_focus_ring_color'),
  chat_background_color: t('tenant.settings.appearance.componentStyles.labels.chat_background_color'),
  reset_button_color: t('tenant.settings.appearance.componentStyles.labels.reset_button_color'),
}));

const filteredComponentStyleLabels = computed(() => {
  const l = { ...styleKeyLabels.value };
  delete l.launcher_background_color;
  return l;
});

const getPaletteColor = (colorId) => {
  const c = local.value.widget_config.color_palette.find(c => c.id === colorId);
  return c ? c.value : colorId;
};

const addColor = () => {
  local.value.widget_config.color_palette.push({ id: uuidv4(), name: t('tenant.settings.defaults.newColor'), value: '#000000' });
};
const removeColor = (idToRemove) => {
  if (local.value.widget_config.color_palette.length <= 2) {
    addToast(t('tenant.settings.appearance.colorPalette.removeBaseColorError'), 'warning');
    return;
  }
  local.value.widget_config.color_palette = local.value.widget_config.color_palette.filter(c => c.id !== idToRemove);
};
const removeFile = (field) => {
  local.value.widget_config[field] = null;
  const el = document.getElementById(field);
  if (el) el.value = '';
  addToast(t('tenant.settings.actions.imageRemoved'), 'success');
};
const handleFileUpload = async (event, field) => {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => { local.value.widget_config[field] = reader.result; addToast(t('tenant.settings.actions.imageUpdated'), 'success'); };
  reader.onerror = () => addToast(t('tenant.settings.actions.readFailed'), 'error');
  reader.readAsDataURL(file);
};
const copyScript = () => {
  const script = `<script src="${props.apiUrl}/tenants/widget.js" data-tenant-id="${props.tenantId}"><\/script>`;
  navigator.clipboard.writeText(script)
    .then(() => addToast(t('tenant.settings.actions.scriptCopied'), 'success'))
    .catch(() => addToast(t('tenant.settings.actions.copyFailed'), 'error'));
};
</script>
