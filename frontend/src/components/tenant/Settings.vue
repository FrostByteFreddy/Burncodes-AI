<template>
  <div class="cfg-page">
    <div v-if="!tenantsStore.currentTenant" class="cfg-layout" aria-busy="true">
      <div class="cfg-stack">
        <Skeleton class="ghost--title" style="width: 160px; height: 28px" />
        <BcPanel as="section"  v-for="n in 3" :key="n" class="ghost-stack">
          <Skeleton class="ghost--title" style="width: 140px" />
          <Skeleton style="height: 40px" />
          <Skeleton class="ghost--line" style="width: 60%" />
        </BcPanel>
      </div>
      <div class="cfg-preview"><Skeleton style="height: 100%; border-radius: 20px" /></div>
    </div>

    <div v-else class="cfg-layout">
      <form class="cfg-form" @submit.prevent="save">
        <div class="page-head">
          <div>
            <h1 class="page-title">{{ $t('pages.configureTitle') }}</h1>
            <p class="page-lede">{{ $t('pages.configure') }}</p>
          </div>
          <div class="page-actions">
            <BcButton variant="secondary" type="button"  :disabled="matching" @click="matchWebsite">
              <font-awesome-icon :icon="matching ? ['fas', 'spinner'] : ['fas', 'wand-magic-sparkles']" :class="{ 'animate-spin': matching }" />
              {{ $t('configure.branding.button') }}
            </BcButton>
          </div>
        </div>

        <ConversationTab :model-value="formData" />

        <!-- Appears once something changed; one save for both tabs -->
        <Transition name="cfg-bar">
          <div v-if="dirty" class="cfg-savebar" role="status">
            <p>{{ $t('configure.unsaved') }}</p>
            <div class="page-actions">
              <BcButton variant="secondary" type="button"  :disabled="saving" @click="load">{{ $t('configure.discard') }}</BcButton>
              <BcButton variant="primary" type="submit"  :disabled="saving">
                <Spinner v-if="saving" data-icon="inline-start" />
                {{ $t('configure.save') }}
              </BcButton>
            </div>
          </div>
        </Transition>
      </form>

      <aside class="cfg-preview" :aria-label="$t('configure.preview')">
        <EditablePreview :form="formData" :tenant-id="tenantsStore.currentTenant?.id || ''" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { Spinner } from '@/components/ui/spinner';
import { Skeleton } from '@/components/ui/skeleton';
import { BcButton, BcPanel } from '@/components/ui';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import apiClient from '../../utils/api';
import ConversationTab from './settings/ConversationTab.vue';
import EditablePreview from './settings/EditablePreview.vue';
import { applyBranding, fromTenant } from '../../utils/widgetConfig';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();

const saving = ref(false);

const formData = ref(fromTenant({}));
const snapshot = ref('');
const dirty = computed(() => snapshot.value !== '' && JSON.stringify(formData.value) !== snapshot.value);

const load = () => {
  const tenant = tenantsStore.currentTenant;
  if (!tenant) return;
  formData.value = fromTenant(tenant);
  snapshot.value = JSON.stringify(formData.value);
};
// The store first shows the copy cached in the browser, then the fresh one from
// the server: take the fresh one too, unless the user already started editing.
watch(() => tenantsStore.currentTenant, (tenant, previous) => {
  if (!dirty.value || tenant?.id !== previous?.id) load();
}, { immediate: true });

const save = async () => {
  if (!tenantsStore.currentTenant || saving.value) return;
  saving.value = true;
  try {
    // the audience is set under Einstellungen › Chatbots; only the preview reads it here
    const { audience, ...changes } = formData.value;
    await tenantsStore.updateTenant(tenantsStore.currentTenant.id, changes);
    snapshot.value = JSON.stringify(formData.value);
    addToast(t('configure.saved'), 'success');
  } catch {
    addToast(t('tenant.settings.actions.saveFailed'), 'error');
  } finally {
    saving.value = false;
  }
};

// ── Look taken from the website ─────────────────────────────────────
// Nothing is saved until the customer saves.
const matching = ref(false);

const matchWebsite = async () => {
  const tenantId = tenantsStore.currentTenant?.id;
  if (!tenantId || matching.value) return;
  matching.value = true;
  try {
    const { data } = await apiClient.post(`/tenants/${tenantId}/branding`, {});
    const found = applyBranding(formData.value.widget_config, data);
    if (found) addToast(t('configure.branding.applied', { site: new URL(data.source_url).hostname }), 'success');
    else addToast(t('configure.branding.nothing'), 'warning');
  } catch (err) {
    const code = err.response?.data?.error;
    addToast(t(code === 'no_website' ? 'configure.branding.noWebsite' : 'configure.branding.failed'), 'error');
  } finally {
    matching.value = false;
  }
};

// Closing the tab with unsaved changes asks the browser to confirm
const onBeforeUnload = (e) => { if (dirty.value) { e.preventDefault(); e.returnValue = ''; } };
onMounted(() => window.addEventListener('beforeunload', onBeforeUnload));
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload));
</script>

<style scoped>
/* Settings and preview share the width evenly */
.cfg-layout { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 32px; align-items: start; }
.cfg-form { min-width: 0; }

.cfg-savebar {
  position: sticky; bottom: 32px; z-index: 20;
  display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  margin-top: 20px; padding: 16px 16px 16px 20px;
  border-radius: var(--radius-lg);
  background: var(--surface-2); border: 1px solid var(--interactive-strong);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}
.cfg-savebar p { font-size: 16px; font-weight: 600; color: var(--surface-heading); }
.cfg-bar-enter-active, .cfg-bar-leave-active { transition: opacity var(--t-fast), transform var(--t-fast); }
.cfg-bar-enter-from, .cfg-bar-leave-to { opacity: 0; transform: translateY(8px); }

/* Full viewport height minus the shell's top and bottom padding */
.cfg-preview {
  position: sticky; top: 40px;
  height: calc(100dvh - 80px);
  display: flex; flex-direction: column;
}

@media (max-width: 1100px) {
  .cfg-layout { grid-template-columns: minmax(0, 1fr); }
  .cfg-preview { position: static; order: -1; height: 70dvh; }
}
</style>
