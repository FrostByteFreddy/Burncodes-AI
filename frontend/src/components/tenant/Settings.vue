<template>
  <div>
    <div class="tab-bar">
      <button type="button" @click="activeTab = 'behavior'"
        class="tab-bar__btn"
        :class="activeTab === 'behavior' ? 'btn-primary shadow-sm' : 'btn-ghost'">
        <font-awesome-icon :icon="['fas', 'sliders']" />{{ $t("tenant.settings.tabs.behavior") }}
      </button>
      <button type="button" @click="activeTab = 'appearance'"
        class="tab-bar__btn"
        :class="activeTab === 'appearance' ? 'btn-primary shadow-sm' : 'btn-ghost'">
        <font-awesome-icon :icon="['fas', 'palette']" />{{ $t("tenant.settings.tabs.appearance") }}
      </button>
      <button type="button" @click="activeTab = 'rules'"
        class="tab-bar__btn"
        :class="activeTab === 'rules' ? 'btn-primary shadow-sm' : 'btn-ghost'">
        <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" />{{ $t("tenant.settings.tabs.rules") }}
      </button>
    </div>

    <form @submit.prevent="handleUpdate" class="space-y-6 mt-6">
      <div v-show="activeTab === 'behavior'">
        <BehaviorTab v-model="formData" />
      </div>
      <div v-show="activeTab === 'appearance'" @change="handleUpdate">
        <AppearanceTab v-model="formData" :tenant-id="tenantsStore.currentTenant?.id" :preview-key="previewKey" :api-url="apiUrl" />
      </div>
      <div v-show="activeTab === 'rules'">
        <RulesTab />
      </div>

      <div v-show="activeTab === 'behavior'" class="settings-footer">
        <button type="submit" class="btn btn-primary" :disabled="tenantsStore.loading">
          <font-awesome-icon :icon="['fas', 'floppy-disk']" />
          {{ $t("tenant.settings.actions.save") }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import { useI18n } from 'vue-i18n';
import BehaviorTab from './settings/BehaviorTab.vue';
import AppearanceTab from './settings/AppearanceTab.vue';
import RulesTab from './settings/RulesTab.vue';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();

const activeTab = ref('behavior');
const previewKey = ref(0);
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const defaultWidgetConfig = () => ({
  chatbot_title: '',
  logo: null,
  launcher_icon: null,
  show_reset_button: true,
  input_placeholder: 'Send a message...',
  thinking_messages: ['Thinking...', 'Just a moment...', 'Let me check that for you...'],
  color_palette: [
    { id: 'c_white',     name: t('tenant.settings.defaults.white'),     value: '#FFFFFF' },
    { id: 'c_black',     name: t('tenant.settings.defaults.black'),     value: '#1F2937' },
    { id: 'c_primary',   name: t('tenant.settings.defaults.primary'),   value: '#A855F7' },
    { id: 'c_secondary', name: t('tenant.settings.defaults.secondary'), value: '#F3F4F6' },
  ],
  component_styles: {
    header_background_color: 'c_secondary', header_text_color: 'c_black',
    user_message_background_color: 'c_primary', user_message_text_color: 'c_white',
    bot_message_background_color: 'c_secondary', bot_message_text_color: 'c_black',
    send_button_background_color: 'c_primary', send_button_text_color: 'c_white',
    input_background_color: 'c_secondary', input_text_color: 'c_black',
    input_focus_ring_color: 'c_primary', chat_background_color: 'c_white',
    reset_button_color: 'c_primary', launcher_background_color: 'c_primary',
  },
});

const formData = ref({
  name: '', intro_message: '', system_persona: '', rag_prompt_template: '',
  doc_language: 'en', translation_target: 'en', crawl_mode: 'playwright_llm',
  widget_config: defaultWidgetConfig(),
});

watch(() => tenantsStore.currentTenant?.id, () => {
  const tenant = tenantsStore.currentTenant;
  if (!tenant) return;
  const cfg = { ...defaultWidgetConfig(), ...(tenant.widget_config || {}) };
  cfg.color_palette = tenant.widget_config?.color_palette || defaultWidgetConfig().color_palette;
  cfg.component_styles = { ...defaultWidgetConfig().component_styles, ...(tenant.widget_config?.component_styles || {}) };
  formData.value = {
    name: tenant.name, intro_message: tenant.intro_message, system_persona: tenant.system_persona,
    rag_prompt_template: tenant.rag_prompt_template, doc_language: tenant.doc_language,
    translation_target: tenant.translation_target, crawl_mode: tenant.crawl_mode || 'playwright_llm',
    widget_config: cfg,
  };
}, { immediate: true });

const handleUpdate = async () => {
  if (!tenantsStore.currentTenant || tenantsStore.loading) return;
  try {
    await tenantsStore.updateTenant(tenantsStore.currentTenant.id, formData.value);
    addToast(t('tenant.settings.actions.savedSuccess'), 'success');
    previewKey.value++;
  } catch {
    addToast(t('tenant.settings.actions.saveFailed'), 'error');
  }
};
</script>
