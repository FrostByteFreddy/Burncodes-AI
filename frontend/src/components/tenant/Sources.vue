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
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
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
// Live polling — refresh sources every 5 s while a crawl is active
// KPIs are computed from the Pinia store, so they update automatically.
// ---------------------------------------------------------------------------
const liveInterval = ref(null);
const hasActiveJobs = computed(() => crawlingJobs.value.some(j => j.status === 'IN_PROGRESS'));

const startLiveRefresh = () => {
  if (liveInterval.value) return;
  liveInterval.value = setInterval(async () => {
    if (tenantsStore.currentTenant) {
      await tenantsStore.refetch(tenantsStore.currentTenant.id);
    }
  }, 5000);
};

const stopLiveRefresh = () => {
  if (liveInterval.value) { clearInterval(liveInterval.value); liveInterval.value = null; }
};

watch(hasActiveJobs, (active) => { active ? startLiveRefresh() : stopLiveRefresh(); });
onUnmounted(stopLiveRefresh);

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
  } else {
    crawlingJobs.value = [];
  }
}, { immediate: true });

const onCrawlStarted = async () => { await fetchCrawlingJobs(); };
const onUploadDone   = async () => { await tenantsStore.refetch(tenantsStore.currentTenant.id); };

const handleJobCompletion = async () => {
  addToast(t('tenant.sources.actions.crawlCompleted'), 'success');
  await tenantsStore.refetch(tenantsStore.currentTenant.id);
  await fetchCrawlingJobs();
};
const handleJobCancelled = async () => { await fetchCrawlingJobs(); };
const handleJobDeleted   = async () => {
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
