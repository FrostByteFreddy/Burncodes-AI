<template>
  <div class="cfg-page">
    <div class="cfg-layout">
      <form class="cfg-form" @submit.prevent="save">
        <div class="page-head">
          <div>
            <h1 class="page-title">{{ $t('pages.configureTitle') }}</h1>
            <p class="page-lede">{{ $t('pages.configure') }}</p>
          </div>
        </div>

        <div class="cfg-tabs" role="tablist">
          <button
            v-for="tab in TABS"
            :key="tab"
            type="button"
            role="tab"
            class="cfg-tabs__btn"
            :class="{ 'cfg-tabs__btn--active': activeTab === tab }"
            :aria-selected="activeTab === tab"
            @click="activeTab = tab"
          >{{ $t(`configure.tabs.${tab}`) }}</button>
        </div>

        <ConversationTab v-show="activeTab === 'conversation'" :model-value="formData" />
        <LookTab v-show="activeTab === 'look'" :model-value="formData" />

        <!-- Appears once something changed; one save for both tabs -->
        <Transition name="cfg-bar">
          <div v-if="dirty" class="cfg-savebar" role="status">
            <p>{{ $t('configure.unsaved') }}</p>
            <div class="page-actions">
              <button type="button" class="btn-quiet" :disabled="saving" @click="load">{{ $t('configure.discard') }}</button>
              <button type="submit" class="btn-action" :disabled="saving">
                <font-awesome-icon v-if="saving" :icon="['fas', 'spinner']" class="animate-spin" />
                {{ $t('configure.save') }}
              </button>
            </div>
          </div>
        </Transition>
      </form>

      <aside class="cfg-preview" :aria-label="$t('configure.preview')">
        <p class="meta cfg-preview__label">{{ $t('configure.preview') }}</p>
        <div class="cfg-preview__frame">
          <EditablePreview :config="formData.widget_config" :tenant-id="tenantsStore.currentTenant?.id || ''" />
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import ConversationTab from './settings/ConversationTab.vue';
import LookTab from './settings/LookTab.vue';
import EditablePreview from './settings/EditablePreview.vue';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();

const TABS = ['conversation', 'look'];
const activeTab = ref('conversation');
const saving = ref(false);

const defaultWidgetConfig = () => ({
  chatbot_title: '',
  logo: null,
  launcher_icon: null,
  show_reset_button: true,
  show_share_button: false,
  widget_enabled: true,
  input_placeholder: '',
  thinking_messages: [],
  conversation_starters: [],
  starter_background_color: 'c_primary',
  starter_text_color: 'c_white',
  color_palette: [
    { id: 'c_primary',   name: 'Primary',   value: '#5F6DFF' },
    { id: 'c_secondary', name: 'Secondary', value: '#F3F4F6' },
    { id: 'c_black',     name: 'Black',     value: '#1F2937' },
    { id: 'c_white',     name: 'White',     value: '#FFFFFF' },
  ],
  component_styles: {
    header_background_color: 'c_secondary', header_text_color: 'c_black',
    user_message_background_color: 'c_primary', user_message_text_color: 'c_white',
    bot_message_background_color: 'c_secondary', bot_message_text_color: 'c_black',
    send_button_background_color: 'c_primary', send_button_text_color: 'c_white',
    input_background_color: 'c_secondary', input_text_color: 'c_black',
    input_focus_ring_color: 'c_primary', chat_background_color: 'c_white',
    reset_button_color: 'c_primary', reset_button_icon_color: 'c_white',
    close_button_background_color: 'c_primary', close_button_icon_color: 'c_white',
    share_button_color: 'c_primary', share_button_icon_color: 'c_white',
    launcher_background_color: 'c_primary',
  },
});

const FIELDS = ['name', 'intro_message', 'system_persona', 'rag_prompt_template', 'doc_language', 'translation_target'];

// Plain deep copy; store objects are reactive proxies, which structuredClone rejects
const clone = (v) => JSON.parse(JSON.stringify(v));

const fromTenant = (tenant) => {
  const saved = tenant.widget_config || {};
  const base = defaultWidgetConfig();
  return {
    ...Object.fromEntries(FIELDS.map((f) => [f, tenant[f] ?? ''])),
    widget_config: {
      ...base,
      ...clone(saved),
      color_palette: clone(saved.color_palette || base.color_palette),
      component_styles: { ...base.component_styles, ...(saved.component_styles || {}) },
    },
  };
};

const formData = ref(fromTenant({}));
const snapshot = ref('');
const dirty = computed(() => snapshot.value !== '' && JSON.stringify(formData.value) !== snapshot.value);

const load = () => {
  const tenant = tenantsStore.currentTenant;
  if (!tenant) return;
  formData.value = fromTenant(tenant);
  snapshot.value = JSON.stringify(formData.value);
};
watch(() => tenantsStore.currentTenant?.id, load, { immediate: true });

const save = async () => {
  if (!tenantsStore.currentTenant || saving.value) return;
  saving.value = true;
  try {
    await tenantsStore.updateTenant(tenantsStore.currentTenant.id, formData.value);
    snapshot.value = JSON.stringify(formData.value);
    addToast(t('configure.saved'), 'success');
  } catch {
    addToast(t('tenant.settings.actions.saveFailed'), 'error');
  } finally {
    saving.value = false;
  }
};

// Closing the tab with unsaved changes asks the browser to confirm
const onBeforeUnload = (e) => { if (dirty.value) { e.preventDefault(); e.returnValue = ''; } };
onMounted(() => window.addEventListener('beforeunload', onBeforeUnload));
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload));
</script>

<style scoped>
/* Settings get a readable column; the preview takes every remaining pixel */
.cfg-layout { display: grid; grid-template-columns: minmax(0, 600px) minmax(360px, 1fr); gap: 32px; align-items: start; }
.cfg-form { min-width: 0; }

.cfg-tabs {
  display: inline-flex; gap: 4px; padding: 4px; margin-bottom: 20px;
  border-radius: var(--radius-pill); background: var(--surface-1); border: 1px solid var(--surface-3);
}
.cfg-tabs__btn {
  padding: 8px 18px; border: none; border-radius: var(--radius-pill);
  background: none; color: var(--surface-muted); font: inherit; font-size: 15px; font-weight: 600; cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast);
}
.cfg-tabs__btn:hover { color: var(--surface-heading); }
.cfg-tabs__btn--active { background: var(--interactive-strong); color: #fff; }

.cfg-savebar {
  position: sticky; bottom: 32px; z-index: 20;
  display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  margin-top: 20px; padding: 14px 16px 14px 20px;
  border-radius: var(--radius-lg);
  background: var(--surface-2); border: 1px solid var(--interactive-strong);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}
.cfg-savebar p { font-size: 15px; font-weight: 600; color: var(--surface-heading); }
.cfg-bar-enter-active, .cfg-bar-leave-active { transition: opacity var(--t-fast), transform var(--t-fast); }
.cfg-bar-enter-from, .cfg-bar-leave-to { opacity: 0; transform: translateY(8px); }

/* Full viewport height minus the shell's top and bottom padding */
.cfg-preview {
  position: sticky; top: 40px;
  height: calc(100dvh - 80px);
  display: flex; flex-direction: column;
}
.cfg-preview__label { margin-bottom: 8px; }
.cfg-preview__frame { flex: 1; min-height: 0; }

@media (max-width: 1100px) {
  .cfg-layout { grid-template-columns: minmax(0, 1fr); }
  .cfg-preview { position: static; order: -1; height: 70dvh; }
}
</style>
