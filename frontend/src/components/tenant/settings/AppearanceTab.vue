<template>
  <div class="space-y-8">

        <!-- 1. Color Palette -->
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

        <!-- 2. Header -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'rectangle-ad']" class="settings-section__icon" />
            {{ $t('tenant.settings.appearance.header.title') }}
          </h3>
          <div class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              <div>
                <label for="header_background_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.header_background_color') }}</label>
                <select v-model="local.widget_config.component_styles.header_background_color" id="header_background_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
                <p class="step-subtext mt-1">{{ $t('tenant.settings.appearance.header.bgHint') }}</p>
              </div>
              <div>
                <label for="header_text_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.header_text_color') }}</label>
                <select v-model="local.widget_config.component_styles.header_text_color" id="header_text_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="reset_button_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.reset_button_color') }}</label>
                <select v-model="local.widget_config.component_styles.reset_button_color" id="reset_button_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="reset_button_icon_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.reset_button_icon_color') }}</label>
                <select v-model="local.widget_config.component_styles.reset_button_icon_color" id="reset_button_icon_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="close_button_background_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.close_button_background_color') }}</label>
                <select v-model="local.widget_config.component_styles.close_button_background_color" id="close_button_background_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="close_button_icon_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.close_button_icon_color') }}</label>
                <select v-model="local.widget_config.component_styles.close_button_icon_color" id="close_button_icon_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
            </div>
            <div>
              <label for="chatbot_title" class="form-field">{{ $t('tenant.settings.appearance.chatWindow.chatbotTitle') }}</label>
              <input v-model="local.widget_config.chatbot_title" type="text" id="chatbot_title" class="form-input" />
            </div>
            <div>
              <label for="logo" class="form-field">{{ $t('tenant.settings.appearance.chatWindow.logo') }}</label>
              <div class="file-input-row">
                <input @change="handleFileUpload($event, 'logo')" type="file" id="logo" accept="image/*,.svg" class="file-input" />
                <button v-if="local.widget_config.logo" @click.prevent="removeFile('logo')" class="starter-delete-btn">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
              <img v-if="local.widget_config.logo" :src="local.widget_config.logo" class="file-preview-img" />
            </div>
            <div class="checkbox-field">
              <input v-model="local.widget_config.show_reset_button" type="checkbox" id="show_reset_button" class="checkbox-field__input" />
              <label for="show_reset_button" class="checkbox-field__label">{{ $t('tenant.settings.appearance.chatWindow.showResetButton') }}</label>
            </div>
          </div>
        </div>

        <!-- 3. Messages -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'comment-dots']" class="settings-section__icon" />
            {{ $t('tenant.settings.appearance.messages.title') }}
          </h3>
          <div class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              <div>
                <label for="chat_background_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.chat_background_color') }}</label>
                <select v-model="local.widget_config.component_styles.chat_background_color" id="chat_background_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div></div>
              <div>
                <label for="bot_message_background_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.bot_message_background_color') }}</label>
                <select v-model="local.widget_config.component_styles.bot_message_background_color" id="bot_message_background_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="user_message_background_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.user_message_background_color') }}</label>
                <select v-model="local.widget_config.component_styles.user_message_background_color" id="user_message_background_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="bot_message_text_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.bot_message_text_color') }}</label>
                <select v-model="local.widget_config.component_styles.bot_message_text_color" id="bot_message_text_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="user_message_text_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.user_message_text_color') }}</label>
                <select v-model="local.widget_config.component_styles.user_message_text_color" id="user_message_text_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
            </div>
            <div>
              <label for="thinking_messages" class="form-field">{{ $t('tenant.settings.appearance.chatWindow.thinkingMessages') }}</label>
              <AutoGrowTextarea v-model="thinkingMessages" id="thinking_messages" rows="3"
                :placeholder="$t('tenant.settings.appearance.chatWindow.thinkingPlaceholder')"
                class="form-input" />
            </div>
          </div>
        </div>

        <!-- 4. Input Field -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'keyboard']" class="settings-section__icon" />
            {{ $t('tenant.settings.appearance.inputField.title') }}
          </h3>
          <div class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              <div>
                <label for="input_background_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.input_background_color') }}</label>
                <select v-model="local.widget_config.component_styles.input_background_color" id="input_background_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="input_text_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.input_text_color') }}</label>
                <select v-model="local.widget_config.component_styles.input_text_color" id="input_text_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="input_focus_ring_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.input_focus_ring_color') }}</label>
                <select v-model="local.widget_config.component_styles.input_focus_ring_color" id="input_focus_ring_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="send_button_background_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.send_button_background_color') }}</label>
                <select v-model="local.widget_config.component_styles.send_button_background_color" id="send_button_background_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div>
                <label for="send_button_text_color" class="form-field">{{ $t('tenant.settings.appearance.componentStyles.labels.send_button_text_color') }}</label>
                <select v-model="local.widget_config.component_styles.send_button_text_color" id="send_button_text_color" class="form-input">
                  <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
            </div>
            <div>
              <label for="input_placeholder" class="form-field">{{ $t('tenant.settings.appearance.chatWindow.inputPlaceholder') }}</label>
              <input v-model="local.widget_config.input_placeholder" type="text" id="input_placeholder" class="form-input" />
            </div>
          </div>
        </div>

        <!-- 5. Conversation Starters -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'bolt']" class="settings-section__icon" />
            Conversation Starters
          </h3>
          <p class="step-subtext mb-4">Clickable prompt chips shown before the first user message, aligned to the right.</p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 mb-5">
            <div>
              <label for="starter_bg" class="form-field">Chip Background</label>
              <select v-model="local.widget_config.starter_background_color" id="starter_bg" class="form-input">
                <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label for="starter_text" class="form-field">Chip Text</label>
              <select v-model="local.widget_config.starter_text_color" id="starter_text" class="form-input">
                <option v-for="c in local.widget_config.color_palette" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </div>

          <div class="starters-list">
            <div v-for="starter in local.widget_config.conversation_starters" :key="starter.id" class="starter-row">
              <input v-model="starter.label" type="text" placeholder="What can I help you with?" class="form-input flex-1" />
              <button type="button" @click.prevent="removeStarter(starter.id)" class="starter-delete-btn">
                <font-awesome-icon :icon="['fas', 'trash']" />
              </button>
            </div>
          </div>

          <button type="button" @click.prevent="addStarter" class="starter-add-btn">
            <font-awesome-icon :icon="['fas', 'plus']" />
            Add Starter
          </button>
        </div>

        <!-- 6. Launcher -->
        <div class="settings-section">
          <h3 class="settings-section__title">
            <font-awesome-icon :icon="['fas', 'rocket']" class="settings-section__icon" />
            {{ $t('tenant.settings.appearance.launcher.title') }}
          </h3>
          <div class="space-y-6">
            <!-- Widget enabled toggle -->
            <div class="checkbox-field">
              <input
                v-model="local.widget_config.widget_enabled"
                type="checkbox"
                id="widget_enabled"
                class="checkbox-field__input"
              />
              <label for="widget_enabled" class="checkbox-field__label">
                {{ $t('tenant.settings.appearance.launcher.widgetEnabled') }}
              </label>
            </div>
            <p class="step-subtext -mt-4">{{ $t('tenant.settings.appearance.launcher.widgetEnabledHint') }}</p>

            <div :class="{ 'opacity-50 pointer-events-none': local.widget_config.widget_enabled === false }">
            <div>
              <label for="launcher_icon" class="form-field">{{ $t('tenant.settings.appearance.launcher.icon') }}</label>
              <div class="file-input-row">
                <input @change="handleFileUpload($event, 'launcher_icon')" type="file" id="launcher_icon" accept="image/*,.svg" class="file-input" />
                <button v-if="local.widget_config.launcher_icon" @click.prevent="removeFile('launcher_icon')" class="starter-delete-btn">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
              <div v-if="local.widget_config.launcher_icon" class="mt-4">
                <p class="launcher-icon-caption">{{ $t('tenant.settings.appearance.launcher.currentIcon') }}</p>
                <img :src="local.widget_config.launcher_icon" class="launcher-icon-preview" />
              </div>
            </div>
            <div>
              <label for="launcher_background_color" class="form-field">{{ $t('tenant.settings.appearance.launcher.backgroundColor') }}</label>
              <select v-model="local.widget_config.component_styles.launcher_background_color" id="launcher_background_color" class="form-input">
                <option v-for="color in local.widget_config.color_palette" :key="color.id" :value="color.id">{{ color.name }}</option>
              </select>
            </div>
            <div class="launcher-inline-preview">
              <span class="form-field">{{ $t('tenant.settings.appearance.preview.launcher') }}</span>
              <LauncherPreview
                :icon="local.widget_config.launcher_icon"
                :background-color="getPaletteColor(local.widget_config.component_styles.launcher_background_color)"
              />
            </div>
            </div> <!-- /conditional dimmer -->
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
import LauncherPreview from '../LauncherPreview.vue';

const props = defineProps({
  modelValue: { type: Object, required: true },
  tenantId: { type: String, required: true },
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

const getPaletteColor = (colorId) => {
  const c = local.value.widget_config.color_palette.find(c => c.id === colorId);
  return c ? c.value : colorId;
};

const addColor    = () => { local.value.widget_config.color_palette.push({ id: uuidv4(), name: t('tenant.settings.defaults.newColor'), value: '#000000' }); };
const removeColor = (idToRemove) => {
  if (local.value.widget_config.color_palette.length <= 2) { addToast(t('tenant.settings.appearance.colorPalette.removeBaseColorError'), 'warning'); return; }
  local.value.widget_config.color_palette = local.value.widget_config.color_palette.filter(c => c.id !== idToRemove);
};
const addStarter = () => {
  if (!local.value.widget_config.conversation_starters) local.value.widget_config.conversation_starters = [];
  local.value.widget_config.conversation_starters.push({ id: uuidv4(), label: '' });
};
const removeStarter = (id) => {
  local.value.widget_config.conversation_starters =
    local.value.widget_config.conversation_starters.filter(s => s.id !== id);
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
</script>
