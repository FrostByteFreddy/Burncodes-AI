<template>
  <div class="sources-panel">
    <KnowledgeList
      :crawling-jobs="crawlingJobs"
      @delete="confirmDelete"
      @job-completed="handleJobCompletion"
      @job-cancelled="handleJobCancelled"
    />

    <div class="sources-sidebar">
      <div class="sources-sidebar__sticky">
        <button @click="wizardOpen = true" class="add-knowledge-btn group">
          <div class="add-knowledge-btn__icon">
            <font-awesome-icon :icon="['fas', 'plus']" />
          </div>
          <div class="text-center">
            <p class="add-knowledge-btn__label">{{ $t('tenant.sources.wizard.addKnowledge') }}</p>
            <p class="add-knowledge-btn__sub">Website or document</p>
          </div>
        </button>
      </div>
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
import { ref, watch } from 'vue';
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

const wizardOpen = ref(false);
const crawlingJobs = ref([]);
const sourceToDelete = ref(null);
const showConfirmationModal = ref(false);

const fetchCrawlingJobs = async () => {
  if (!tenantsStore.currentTenant) return;
  try {
    const r = await apiClient.get(`/tenants/${tenantsStore.currentTenant.id}/crawling_jobs`);
    crawlingJobs.value = r.data;
  } catch { addToast(t('tenant.sources.actions.fetchFailed'), 'error'); }
};

watch(() => tenantsStore.currentTenant, (t) => {
  if (t) fetchCrawlingJobs(); else crawlingJobs.value = [];
}, { immediate: true });

const onCrawlStarted = async () => { await fetchCrawlingJobs(); };
const onUploadDone  = async () => { await tenantsStore.refetch(tenantsStore.currentTenant.id); };

const handleJobCompletion = async () => {
  addToast(t('tenant.sources.actions.crawlCompleted'), 'success');
  await tenantsStore.refetch(tenantsStore.currentTenant.id);
  await fetchCrawlingJobs();
};
const handleJobCancelled = async () => { await fetchCrawlingJobs(); };

const confirmDelete = (source) => { sourceToDelete.value = source; showConfirmationModal.value = true; };
const cancelDelete  = () => { sourceToDelete.value = null; showConfirmationModal.value = false; };

const handleDelete = async () => {
  if (!tenantsStore.currentTenant || !sourceToDelete.value) return;
  const id = sourceToDelete.value.id;
  const orig = [...tenantsStore.currentTenant.tenant_sources];
  const idx = orig.findIndex(s => s.id === id);
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
