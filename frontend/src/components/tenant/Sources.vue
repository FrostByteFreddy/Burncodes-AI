<template>
  <div class="grid grid-cols-1 xl:grid-cols-12 xl:rounded-3xl bg-base-100 xl:border border-base-200/50 xl:shadow-sm gap-0 min-h-[calc(100vh-10rem)]">

    <!-- Left: knowledge list -->
    <KnowledgeList
      :crawling-jobs="crawlingJobs"
      @delete="confirmDelete"
      @job-completed="handleJobCompletion"
      @job-cancelled="handleJobCancelled"
    />

    <!-- Right: clickable Add Knowledge zone -->
    <div class="xl:col-span-5 border-t xl:border-t-0 xl:border-l border-base-200/50 p-6">
      <div class="sticky top-6">
        <button
          @click="wizardOpen = true"
          class="w-full border-2 border-dashed border-base-200 hover:border-primary/50 bg-base-200/20 hover:bg-primary/5 transition-all duration-300 rounded-2xl flex flex-col items-center justify-center gap-4 py-12 group cursor-pointer"
        >
          <div class="w-14 h-14 rounded-2xl bg-base-200 group-hover:bg-primary/10 transition-colors flex items-center justify-center text-2xl text-base-content/30 group-hover:text-primary">
            <font-awesome-icon :icon="['fas', 'plus']" />
          </div>
          <div class="text-center">
            <p class="text-sm font-bold text-base-content/50 group-hover:text-base-content transition-colors">{{ $t('tenant.sources.wizard.addKnowledge') }}</p>
            <p class="text-xs text-base-content/30 mt-1">Website or document</p>
          </div>
        </button>
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
