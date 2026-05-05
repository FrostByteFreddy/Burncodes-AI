<template>
  <div class="grid grid-cols-1 xl:grid-cols-12 xl:rounded-3xl bg-base-100 xl:border border-base-200/50 xl:shadow-sm overflow-hidden min-h-[calc(100vh-10rem)]">

    <!-- Left: knowledge list -->
    <KnowledgeList
      :crawling-jobs="crawlingJobs"
      @delete="confirmDelete"
      @job-completed="handleJobCompletion"
      @job-cancelled="handleJobCancelled"
    />

    <!-- Right: Add Knowledge CTA -->
    <div class="xl:col-span-5 bg-base-200/30 p-6 lg:p-10 flex flex-col h-full border-t xl:border-t-0 border-base-200/50">
      <div class="mb-8">
        <h2 class="text-2xl lg:text-3xl font-display font-bold text-base-content tracking-tight mb-2">Knowledge</h2>
        <p class="text-base-content/60 text-sm">Add websites or documents to your AI's knowledge base.</p>
      </div>

      <div class="flex-1 flex flex-col items-center justify-center">
        <div class="text-center max-w-xs">
          <div class="w-20 h-20 mx-auto mb-6 rounded-3xl bg-primary/10 flex items-center justify-center text-primary text-3xl">
            <font-awesome-icon :icon="['fas', 'plus']" />
          </div>
          <h3 class="text-xl font-bold text-base-content mb-2">Add Knowledge</h3>
          <p class="text-sm text-base-content/50 mb-8 leading-relaxed">
            Index websites or upload documents in a few quick steps.
          </p>
          <button @click="wizardOpen = true" class="btn btn-primary btn-lg w-full rounded-2xl">
            <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
            {{ $t('tenant.sources.wizard.addKnowledge') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Wizard slide-over -->
    <AddKnowledgeWizard
      :open="wizardOpen"
      @close="wizardOpen = false"
      @crawl-started="onCrawlStarted"
      @upload-done="onUploadDone"
    />

    <!-- Delete confirmation -->
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
