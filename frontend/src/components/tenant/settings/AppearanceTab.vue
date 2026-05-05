<template>
  <div class="space-y-8">
    <div class="appearance-grid">
      <!-- Left column -->
      <div class="space-y-8">
        <!-- Color Palette -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'palette']" class="settings-section__icon" />
            {{ $t('tenant.settings.appearance.colorPalette.title') }}
          </h3>
          <p class="step-subtext mb-4">{{ $t('tenant.settings.appearance.colorPalette.description') }}</p>
          <div class="palette-swatches">
            <div v-for="(color, index) in local.widget_config.color_palette" :key="color.id" class="palette-swatch">
              <label class="relative cursor-pointer block">
                <span class="palette-swatch__color" :style="{ backgroundColor: color.value }" />
                <input v-model="color.value" type="color" class="absolute inset-0 opacity-0 w-full h-full cursor-pointer" />
                <button v-if="index > 1" type="button" @click.prevent.stop="removeColor(color.id)"
                  class="palette-swatch__remove">×</button>
              </label>
              <input v-model="color.name" type="text" :disabled="index < 2" class="palette-swatch__name" />
            </div>
            <div class="flex flex-col items-center gap-1.5">
              <button type="button" @click.prevent="addColor" class="palette-add-btn">
                <font-awesome-icon :icon="['fas', 'plus']" />
              </button>
              <span class="palette-add-label">Add</span>
            </div>
          </div>
        </div>

        <!-- Chat Window -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'comment-dots']" class="settings-section__icon" />
            {{ $t("tenant.settings.appearance.chatWindow.title") }}
          </h3>
          <div class="space-y-4">
            <div>
              <label for="chatbot_title" class="form-field">{{ $t("tenant.settings.appearance.chatWindow.chatbotTitle") }}</label>
              <input v-model="local.widget_config.chatbot_title" type="text" id="chatbot_title" class="form-input" />
            </div>
            <div>
              <label for="logo" class="form-field">{{ $t("tenant.settings.appearance.chatWindow.logo") }}</label>
              <div class="file-input-row">
                <input @change="handleFileUpload($event, 'logo')" type="file" id="logo" accept="image/*,.svg" class="file-input" />
                <button v-if="local.widget_config.logo" @click.prevent="removeFile('logo')"
                  class="btn btn-square btn-ghost text-error hover:bg-error/10">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
              <img v-if="local.widget_config.logo" :src="local.widget_config.logo" class="file-preview-img" />
            </div>
            <div class="checkbox-field">
              <input v-model="local.widget_config.show_reset_button" type="checkbox" id="show_reset_button"
                class="checkbox-field__input" />
              <label for="show_reset_button" class="checkbox-field__label">{{ $t("tenant.settings.appearance.chatWindow.showResetButton") }}</label>
            </div>
            <div>
              <label for="input_placeholder" class="form-field">{{ $t("tenant.settings.appearance.chatWindow.inputPlaceholder") }}</label>
              <input v-model="local.widget_config.input_placeholder" type="text" id="input_placeholder" class="form-input" />
            </div>
            <div>
              <label for="thinking_messages" class="form-field">{{ $t("tenant.settings.appearance.chatWindow.thinkingMessages") }}</label>
              <AutoGrowTextarea v-model="thinkingMessages" id="thinking_messages" rows="3"
                :placeholder="$t('tenant.settings.appearance.chatWindow.thinkingPlaceholder')"
                class="form-input" />
            </div>
          </div>
        </div>

        <!-- Component Styles -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'swatchbook']" class="settings-section__icon" />
            {{ $t("tenant.settings.appearance.componentStyles.title") }}
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div v-for="(label, key) in filteredComponentStyleLabels" :key="key">
              <label :for="key" class="form-field">{{ label }}</label>
              <select v-model="local.widget_config.component_styles[key]" :id="key" class="form-input">
                <option v-for="color in local.widget_config.color_palette" :key="color.id" :value="color.id">{{ color.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Launcher -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'rocket']" class="settings-section__icon" />
            {{ $t("tenant.settings.appearance.launcher.title") }}
          </h3>
          <div class="space-y-6">
            <div>
              <label for="launcher_icon" class="form-field">{{ $t("tenant.settings.appearance.launcher.icon") }}</label>
              <div class="file-input-row">
                <input @change="handleFileUpload($event, 'launcher_icon')" type="file" id="launcher_icon" accept="image/*,.svg" class="file-input" />
                <button v-if="local.widget_config.launcher_icon" @click.prevent="removeFile('launcher_icon')"
                  class="btn btn-square btn-ghost text-error hover:bg-error/10">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
              <div v-if="local.widget_config.launcher_icon" class="mt-4">
                <p class="launcher-icon-caption">{{ $t("tenant.settings.appearance.launcher.currentIcon") }}</p>
                <img :src="local.widget_config.launcher_icon" class="launcher-icon-preview" />
              </div>
            </div>
            <div>
              <label for="launcher_background_color" class="form-field">{{ $t("tenant.settings.appearance.launcher.backgroundColor") }}</label>
              <select v-model="local.widget_config.component_styles.launcher_background_color" id="launcher_background_color" class="form-input">
                <option v-for="color in local.widget_config.color_palette" :key="color.id" :value="color.id">{{ color.name }}</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Right column: sticky preview -->
      <div>
        <div class="appearance-preview-col">
          <ChatPreview :tenantId="tenantId" :key="previewKey" />
          <div class="mb-4">
            <h4 class="appearance-preview__label">{{ $t("tenant.settings.appearance.preview.launcher") }}</h4>
            <LauncherPreview :icon="local.widget_config.launcher_icon" :background-color="getPaletteColor(local.widget_config.component_styles.launcher_background_color)" />
          </div>
        </div>
      </div>
    </div>

    <!-- Installation Script -->
    <div class="settings-section mt-2">
      <h3 class="settings-section__title">
        <font-awesome-icon :icon="['fas', 'code']" class="settings-section__icon" />
        {{ $t('tenant.settings.appearance.installation.title') }}
      </h3>
      <p class="step-subtext mb-4">{{ $t('tenant.settings.appearance.installation.instruction') }}</p>
      <div class="install-script-block">
        <pre class="install-script-pre"><code>&lt;script src="{{ apiUrl }}/tenants/widget.js" data-tenant-id="{{ tenantId }}"&gt;&lt;/script&gt;</code></pre>
        <button @click.prevent="copyScript" class="install-script-copy">
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

const addColor    = () => { local.value.widget_config.color_palette.push({ id: uuidv4(), name: t('tenant.settings.defaults.newColor'), value: '#000000' }); };
const removeColor = (idToRemove) => {
  if (local.value.widget_config.color_palette.length <= 2) { addToast(t('tenant.settings.appearance.colorPalette.removeBaseColorError'), 'warning'); return; }
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
  reader.onload  = () => { local.value.widget_config[field] = reader.result; addToast(t('tenant.settings.actions.imageUpdated'), 'success'); };
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
