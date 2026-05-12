<template>
  <div class="sources-page">

    <!-- ═══════════════════════════════════════════════════
         PANEL 1 — Crawls & Documents
    ════════════════════════════════════════════════════ -->
    <div class="knowledge-panel">

      <!-- Panel header -->
      <div class="knowledge-panel__header">
        <div class="knowledge-panel__header-left">
          <div class="knowledge-panel__icon">
            <font-awesome-icon :icon="['fas', 'database']" />
          </div>
          <div>
            <h2 class="knowledge-panel__title">Crawls &amp; Documents</h2>
            <p class="knowledge-panel__sub">Indexed pages, uploaded PDFs and files</p>
          </div>
        </div>
        <button @click="wizardOpen = true" class="panel-add-btn" :title="$t('tenant.sources.wizard.addKnowledge')">
          <font-awesome-icon :icon="['fas', 'plus']" />
        </button>
      </div>

      <!-- Divider -->
      <div class="knowledge-panel__divider"></div>

      <!-- List -->
      <KnowledgeList
        :crawling-jobs="crawlingJobs"
        @delete-source="confirmDelete"
        @job-completed="handleJobCompletion"
        @job-cancelled="handleJobCancelled"
        @job-deleted="handleJobDeleted"
      />
    </div>

    <!-- ═══════════════════════════════════════════════════
         PANEL 2 — Custom Knowledge (Fine-tuning Rules)
    ════════════════════════════════════════════════════ -->
    <div class="knowledge-panel">

      <!-- Panel header -->
      <div class="knowledge-panel__header">
        <div class="knowledge-panel__header-left">
          <div class="knowledge-panel__icon knowledge-panel__icon--accent">
            <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" />
          </div>
          <div>
            <h2 class="knowledge-panel__title">Custom Knowledge</h2>
            <p class="knowledge-panel__sub">Fine-tuning rules that guide how the bot responds to specific triggers</p>
          </div>
        </div>
        <button @click="rulesTabRef?.openModal()" class="panel-add-btn panel-add-btn--accent" title="Add rule">
          <font-awesome-icon :icon="['fas', 'plus']" />
        </button>
      </div>

      <div class="knowledge-panel__divider"></div>

      <!-- Rules -->
      <RulesTab ref="rulesTabRef" />
    </div>

    <AddKnowledgeWizard
      :open="wizardOpen"
      @close="wizardOpen = false"
      @crawl-started="onCrawlStarted"
      @upload-done="onUploadDone"
    />

    <ConfirmationModal
      :show="showConfirmationModal"
      :title="$t('tenant.sources.deleteModal.title')"
      :message="$t('tenant.sources.deleteModal.message', { source: sourceToDelete?.source_location })"
      :confirmButtonText="$t('tenant.sources.deleteModal.confirm')"
      @confirm="handleDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { supabase } from '../../supabase';
import KnowledgeList from './sources/KnowledgeList.vue';
import AddKnowledgeWizard from './sources/AddKnowledgeWizard.vue';
import ConfirmationModal from '../ConfirmationModal.vue';
import RulesTab from './sources/RulesTab.vue';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();

const wizardOpen            = ref(false);
const crawlingJobs          = ref([]);
const sourceToDelete        = ref(null);
const showConfirmationModal = ref(false);
const rulesTabRef           = ref(null);

// ---------------------------------------------------------------------------
// Supabase Realtime — react to crawling_jobs changes for this tenant
// ---------------------------------------------------------------------------
let realtimeChannel = null;

const subscribeToJobs = (tenantId) => {
  // Tear down any previous subscription first
  if (realtimeChannel) {
    supabase.removeChannel(realtimeChannel);
    realtimeChannel = null;
  }

  realtimeChannel = supabase
    .channel(`crawling-jobs-${tenantId}`)
    .on(
      'postgres_changes',
      {
        event: '*',           // INSERT | UPDATE | DELETE
        schema: 'public',
        table: 'crawling_jobs',
        filter: `tenant_id=eq.${tenantId}`,
      },
      async (payload) => {
        // Re-fetch enriched list (includes task_count + sources)
        await fetchCrawlingJobs();

        // If a job just became COMPLETED, also refresh the sources store
        if (payload.eventType === 'UPDATE' && payload.new?.status === 'COMPLETED') {
          addToast(t('tenant.sources.actions.crawlCompleted'), 'success');
          await tenantsStore.refetch(tenantId);
        }
      }
    )
    .subscribe();
};

onUnmounted(() => {
  if (realtimeChannel) supabase.removeChannel(realtimeChannel);
});

// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------
const fetchCrawlingJobs = async () => {
  if (!tenantsStore.currentTenant) return;
  try {
    const r = await apiClient.get(`/tenants/${tenantsStore.currentTenant.id}/crawling_jobs`);
    crawlingJobs.value = r.data;
  } catch { addToast(t('tenant.sources.actions.fetchFailed'), 'error'); }
};

watch(() => tenantsStore.currentTenant, (tenant) => {
  if (tenant) {
    fetchCrawlingJobs();
    subscribeToJobs(tenant.id);
  } else {
    crawlingJobs.value = [];
    if (realtimeChannel) { supabase.removeChannel(realtimeChannel); realtimeChannel = null; }
  }
}, { immediate: true });

const onCrawlStarted = async () => { await fetchCrawlingJobs(); };
const onUploadDone   = async () => { await tenantsStore.refetch(tenantsStore.currentTenant.id); };

// These are now mostly no-ops — realtime handles re-fetching.
// Keep them for optimistic UX (delete needs an immediate local update).
const handleJobCompletion = () => {}; // realtime fires crawlCompleted toast + refetch
const handleJobCancelled  = async () => { await fetchCrawlingJobs(); };
const handleJobDeleted    = async () => {
  await fetchCrawlingJobs();
  await tenantsStore.refetch(tenantsStore.currentTenant.id);
};

const confirmDelete = (source) => { sourceToDelete.value = source; showConfirmationModal.value = true; };
const cancelDelete  = () => { sourceToDelete.value = null; showConfirmationModal.value = false; };

const handleDelete = async () => {
  if (!tenantsStore.currentTenant || !sourceToDelete.value) return;
  const id = sourceToDelete.value.id;
  const orig = [...tenantsStore.currentTenant.tenant_sources];
  const idx  = orig.findIndex(s => s.id === id);
  if (idx > -1) tenantsStore.currentTenant.tenant_sources.splice(idx, 1);
  try {
    await apiClient.delete(`/tenants/${tenantsStore.currentTenant.id}/sources/${id}`);
    addToast(t('tenant.sources.actions.deleteSuccess'), 'success');
  } catch {
    tenantsStore.currentTenant.tenant_sources = orig;
    addToast(t('tenant.sources.actions.deleteFailed'), 'error');
  } finally { cancelDelete(); }
};
</script>
