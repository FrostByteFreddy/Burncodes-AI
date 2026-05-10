<template>
  <div class="sources-page">

    <!-- KPI strip -->
    <div class="sources-kpis">
      <div class="sources-kpi">
        <span class="sources-kpi__value">{{ kpis.pages.toLocaleString() }}</span>
        <span class="sources-kpi__label">
          <font-awesome-icon :icon="['fas', 'globe']" />
          Crawled Pages
        </span>
      </div>
      <div class="sources-kpi">
        <span class="sources-kpi__value">{{ kpis.files.toLocaleString() }}</span>
        <span class="sources-kpi__label">
          <font-awesome-icon :icon="['fas', 'file']" />
          Indexed Documents
        </span>
      </div>
      <div class="sources-kpi sources-kpi--error" v-if="kpis.errors > 0">
        <span class="sources-kpi__value">{{ kpis.errors.toLocaleString() }}</span>
        <span class="sources-kpi__label">
          <font-awesome-icon :icon="['fas', 'circle-xmark']" />
          Errors
        </span>
      </div>
      <div class="sources-kpi" v-else>
        <span class="sources-kpi__value sources-kpi__value--success">{{ kpis.pages + kpis.files > 0 ? '100%' : '—' }}</span>
        <span class="sources-kpi__label">
          <font-awesome-icon :icon="['fas', 'circle-check']" />
          Success Rate
        </span>
      </div>
    </div>

    <!-- Banner add button -->
    <button @click="wizardOpen = true" class="sources-add-banner">
      <div class="sources-add-banner__icon">
        <font-awesome-icon :icon="['fas', 'plus']" />
      </div>
      <div class="sources-add-banner__text">
        <span class="sources-add-banner__title">{{ $t('tenant.sources.wizard.addKnowledge') }}</span>
        <span class="sources-add-banner__sub">Crawl a website · Upload a PDF or document</span>
      </div>
    </button>

    <!-- Danger zone -->
    <div class="sources-danger" v-if="kpis.pages + kpis.files > 0">
      <button @click="showDeleteAllModal = true" class="sources-danger__btn" :disabled="deletingAll">
        <font-awesome-icon :icon="['fas', deletingAll ? 'spinner' : 'trash-can']" :spin="deletingAll" />
        {{ deletingAll ? 'Clearing…' : 'Delete All Knowledge' }}
      </button>
    </div>

    <!-- Main list -->
    <KnowledgeList
      :crawling-jobs="crawlingJobs"
      @delete-source="confirmDelete"
      @job-completed="handleJobCompletion"
      @job-cancelled="handleJobCancelled"
      @job-deleted="handleJobDeleted"
    />

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

    <ConfirmationModal
      :show="showDeleteAllModal"
      title="Delete All Knowledge?"
      message="This will permanently remove all sources from the database AND delete the entire Gemini index. This cannot be undone."
      confirmButtonText="Yes, delete everything"
      @confirm="handleDeleteAll"
      @cancel="showDeleteAllModal = false"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import KnowledgeList from './sources/KnowledgeList.vue';
import AddKnowledgeWizard from './sources/AddKnowledgeWizard.vue';
import ConfirmationModal from '../ConfirmationModal.vue';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();

const wizardOpen            = ref(false);
const crawlingJobs          = ref([]);
const sourceToDelete        = ref(null);
const showConfirmationModal = ref(false);
const showDeleteAllModal    = ref(false);
const deletingAll           = ref(false);

// ---------------------------------------------------------------------------
// Local KPIs (derived from tenant_sources already loaded in the store)
// ---------------------------------------------------------------------------
const kpis = computed(() => {
  const sources = tenantsStore.currentTenant?.tenant_sources || [];
  const completed = sources.filter(s => s.status === 'COMPLETED');
  return {
    pages:  completed.filter(s => s.source_type === 'URL').length,
    files:  completed.filter(s => s.source_type === 'FILE' || s.source_type === 'FILE_URL').length,
    errors: sources.filter(s => s.status === 'ERROR' || s.status === 'UNSUPPORTED').length,
  };
});

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

const handleDeleteAll = async () => {
  if (!tenantsStore.currentTenant) return;
  showDeleteAllModal.value = false;
  deletingAll.value = true;
  try {
    await apiClient.delete(`/tenants/${tenantsStore.currentTenant.id}/sources`);
    addToast('All knowledge deleted.', 'success');
    await tenantsStore.refetch(tenantsStore.currentTenant.id);
    await fetchCrawlingJobs();
  } catch {
    addToast('Failed to delete all knowledge.', 'error');
  } finally {
    deletingAll.value = false;
  }
};
</script>
