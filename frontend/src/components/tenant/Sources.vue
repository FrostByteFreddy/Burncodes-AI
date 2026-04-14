```
<template>
  <div class="grid grid-cols-1 xl:grid-cols-12 xl:rounded-3xl bg-base-100 xl:border border-base-200/50 xl:shadow-sm overflow-hidden min-h-[calc(100vh-10rem)]">
    
    <!-- Left Column: Active Sources Data Hub -->
    <div class="xl:col-span-7 bg-base-100 p-6 lg:p-10 flex flex-col h-full xl:border-r border-base-200/50">
      <div class="mb-8">
        <h2 class="text-3xl font-display font-bold text-base-content tracking-tight mb-2">Active Sources</h2>
        <p class="text-base-content/60 text-sm">Manage the knowledge base context that trains your AI.</p>
      </div>

      <!-- Metrics Row -->
      <div class="grid grid-cols-2 gap-4 mb-10 shrink-0">
        <div class="bg-primary/5 rounded-2xl p-5 border border-primary/10 transition-colors">
          <p class="text-xs font-bold uppercase tracking-widest text-primary/70 mb-1">Total Documents</p>
          <p class="text-4xl font-black text-primary font-display leading-none">{{ fileSources.length }}</p>
        </div>
        <div class="bg-secondary/5 rounded-2xl p-5 border border-secondary/10 transition-colors">
          <p class="text-xs font-bold uppercase tracking-widest text-secondary/70 mb-1">Indexed Links</p>
          <p class="text-4xl font-black text-secondary font-display leading-none">{{ urlSources.length }}</p>
        </div>
      </div>

      <!-- Data List Area -->
      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-10 pb-10">
        
        <!-- Loading State -->
        <div v-if="tenantsStore.loading" class="space-y-4">
          <div v-for="n in 3" :key="n" class="h-16 bg-base-200/50 rounded-xl animate-pulse"></div>
        </div>

        <div v-else>
          <!-- Active Crawling Jobs -->
          <div v-if="crawlingJobs.length > 0" class="mb-10 animate-fade-in">
            <h4 class="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-4 flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              Live Activity
            </h4>
            <div class="space-y-3">
              <div v-for="job in crawlingJobs" :key="job.id" class="bg-base-100 border border-base-200 p-4 rounded-2xl shadow-sm relative overflow-hidden">
                <div class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b"
                 :class="{
                   'from-success/80 to-success/40': job.status === 'COMPLETED',
                   'from-primary/80 to-primary/40': job.status === 'IN_PROGRESS',
                   'from-error/80 to-error/40': job.status === 'FAILED',
                   'from-base-300 to-base-200': !['COMPLETED', 'IN_PROGRESS', 'FAILED'].includes(job.status)
                 }"></div>
                 <div class="pl-4">
                   <p class="font-semibold text-sm truncate text-base-content" :title="job.start_url">{{ job.start_url }}</p>
                   <div class="flex justify-between items-center mt-2">
                     <span class="text-xs font-bold tracking-wider"
                      :class="{
                        'text-success': job.status === 'COMPLETED',
                        'text-primary': job.status === 'IN_PROGRESS',
                        'text-error': job.status === 'FAILED',
                        'text-base-content/50': !['COMPLETED', 'IN_PROGRESS', 'FAILED'].includes(job.status)
                      }">{{ job.status }}</span>
                      <p class="text-xs text-base-content/40 font-medium">
                        {{ new Date(job.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}
                      </p>
                   </div>
                   <div class="mt-3" v-if="job.status === 'IN_PROGRESS'">
                     <CrawlingJobProgress :job="job" :tenantId="tenantsStore.currentTenant.id" @job-completed="handleJobCompletion" />
                   </div>
                 </div>
              </div>
            </div>
          </div>

          <!-- Documents -->
          <div class="mb-10">
             <h4 class="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-4">
               {{ $t("tenant.sources.existing.uploadedFiles") }}
             </h4>
             <div v-if="fileSources.length === 0" class="text-base-content/40 text-sm italic bg-base-200/20 p-4 rounded-xl border border-base-200 border-dashed text-center">
               No documents uploaded yet.
             </div>
             <div class="space-y-2">
               <div v-for="source in fileSources" :key="source.id" class="group bg-base-100 hover:bg-base-200/50 border border-base-200 p-4 rounded-2xl flex justify-between items-center transition-all duration-300">
                 <div class="min-w-0 pr-4">
                   <p class="font-semibold text-sm truncate text-base-content flex items-center gap-3">
                     <font-awesome-icon :icon="['fas', 'file-pdf']" class="text-primary/60" />
                     {{ source.source_location }}
                   </p>
                   <p class="text-xs text-base-content/50 mt-1.5 flex items-center gap-2">
                     <span class="w-1.5 h-1.5 rounded-full" :class="source.status === 'INDEXED' ? 'bg-success' : (source.status === 'ERROR' ? 'bg-error' : 'bg-primary')"></span>
                     {{ source.status }}
                   </p>
                 </div>
                 <button @click="confirmDelete(source)" class="btn btn-ghost btn-sm btn-circle text-base-content/30 hover:text-error hover:bg-error/10 opacity-0 group-hover:opacity-100 transition-opacity">
                   <font-awesome-icon :icon="['fas', 'times']" />
                 </button>
               </div>
             </div>
          </div>

          <!-- Links -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-4">
              {{ $t("tenant.sources.existing.crawledUrls") }}
            </h4>
            <div v-if="urlSources.length === 0" class="text-base-content/40 text-sm italic bg-base-200/20 p-4 rounded-xl border border-base-200 border-dashed text-center">
               No URLs indexed yet.
            </div>
            <div class="space-y-2">
              <div v-for="source in urlSources" :key="source.id" class="group bg-base-100 hover:bg-base-200/50 border border-base-200 p-4 rounded-2xl flex justify-between items-center transition-all duration-300">
                <div class="min-w-0 pr-4">
                  <p class="font-semibold text-sm truncate text-base-content flex items-center gap-3">
                    <font-awesome-icon :icon="['fas', 'globe']" class="text-secondary/60" />
                    {{ source.source_location }}
                  </p>
                  <p class="text-xs text-base-content/50 mt-1.5 flex items-center gap-2">
                     <span class="w-1.5 h-1.5 rounded-full" :class="source.status === 'INDEXED' ? 'bg-success' : (source.status === 'ERROR' ? 'bg-error' : 'bg-primary')"></span>
                     {{ source.status }}
                  </p>
                </div>
                <button @click="confirmDelete(source)" class="btn btn-ghost btn-sm btn-circle text-base-content/30 hover:text-error hover:bg-error/10 opacity-0 group-hover:opacity-100 transition-opacity">
                  <font-awesome-icon :icon="['fas', 'times']" />
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
    
    <!-- Right Column: Ingestion Station -->
    <div class="xl:col-span-5 bg-base-200/30 p-6 lg:p-10 flex flex-col h-full border-t xl:border-t-0 border-base-200/50">
      <div class="mb-8">
        <h2 class="text-2xl lg:text-3xl font-display font-bold text-base-content tracking-tight mb-2">Ingestion Station</h2>
        <p class="text-base-content/60 text-sm">Add documents and URLs to ingest into your AI.</p>
      </div>

      <div class="space-y-6">
        
        <!-- File Upload Card -->
        <div class="bg-base-100 p-6 rounded-3xl shadow-sm border border-base-200 flex flex-col">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
              <font-awesome-icon :icon="['fas', 'upload']" />
            </div>
            <div>
              <h3 class="font-bold text-base-content leading-tight">Upload Document</h3>
              <p class="text-xs text-base-content/50">PDF, TXT, CSV accepted</p>
            </div>
          </div>
          
          <div class="relative border-2 border-dashed border-base-300 hover:border-primary/50 transition-colors p-8 rounded-2xl flex flex-col items-center justify-center bg-base-50 group mb-4">
             <input id="file-upload" type="file" @change="handleFileSelect" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
             <div class="w-12 h-12 rounded-full bg-base-200 group-hover:bg-primary/10 group-hover:text-primary transition-colors flex items-center justify-center text-base-content/40 text-xl mb-3">
               <font-awesome-icon :icon="['fas', 'file-arrow-up']" />
             </div>
             <p class="text-sm font-medium text-base-content/80 text-center px-4" v-if="!selectedFile">Select a file from your computer to ingest.</p>
             <p class="text-sm font-bold text-primary text-center px-4" v-else>{{ selectedFile.name }}</p>
          </div>
          
          <button @click="handleUpload" :disabled="!selectedFile || loading" class="btn btn-primary w-full rounded-xl shadow-sm group">
            <font-awesome-icon :icon="['fas', 'upload']" :class="{'mr-2': !loading, 'animate-bounce': loading}" />
            {{ loading ? 'Ingesting...' : 'Ingest Document' }}
          </button>
        </div>

        <!-- URL Crawling Card -->
        <div class="bg-base-100 p-6 rounded-3xl shadow-sm border border-base-200 flex flex-col">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-2xl bg-secondary/10 flex items-center justify-center text-secondary">
              <font-awesome-icon :icon="['fas', 'globe']" />
            </div>
            <div>
              <h3 class="font-bold text-base-content leading-tight">Crawl Website</h3>
              <p class="text-xs text-base-content/50">Point to a URL to sync content</p>
            </div>
          </div>

          <div class="space-y-4">
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-base-content/40">
                <font-awesome-icon :icon="['fas', 'link']" />
              </div>
              <input v-model="startUrl" id="url-input" type="text" placeholder="https://example.com/docs" class="input input-lg w-full bg-base-200/50 border-transparent focus:border-primary focus:bg-base-100 transition-colors pl-12 rounded-2xl text-sm font-medium" :class="{ 'border-error bg-error/5 focus:border-error': !isUrlValid && startUrl }" />
            </div>
            <p v-if="!isUrlValid && startUrl" class="text-error text-xs px-2">Invalid URL format.</p>

            <div class="bg-base-200/30 p-4 rounded-2xl space-y-3">
              <div class="flex items-center">
                <input type="checkbox" v-model="crawlSinglePageOnly" class="checkbox checkbox-sm checkbox-primary rounded" id="single_crawl_only" />
                <label for="single_crawl_only" class="ml-2 block text-sm font-medium text-base-content/80 cursor-pointer">
                  Crawl this page ONLY (no subpages)
                </label>
              </div>

              <div v-if="!crawlSinglePageOnly" class="animate-fade-in pt-2">
                <label for="excluded-urls-input" class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2 px-1">
                  Exclude Paths (Optional)
                </label>
                <textarea v-model="excludedUrls" id="excluded-urls-input" placeholder="e.g. /login&#10;/dashboard" rows="2" class="w-full p-3 bg-base-100 border border-base-200 rounded-xl text-sm focus:outline-none focus:border-primary/50 transition-colors"></textarea>
              </div>
            </div>

            <button @click="startCrawl" :disabled="!startUrl.trim() || loading || !isUrlValid" class="btn btn-secondary w-full rounded-xl shadow-sm mt-2">
              <font-awesome-icon :icon="['fas', 'spider']" class="mr-2" v-if="!loading"/>
              {{ loading ? 'Starting Crawl...' : 'Start Crawl' }}
            </button>
          </div>
        </div>

      </div>
    </div>
    
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
import { ref, computed, onMounted, watch } from "vue";
import { useTenantsStore } from "../../stores/tenants";
import { useAuthStore } from "../../stores/auth";
import { useToast } from "../../composables/useToast";
import ConfirmationModal from "../ConfirmationModal.vue";
import CrawlingJobProgress from "./CrawlingJobProgress.vue";
import apiClient from "@/utils/api";

import { useI18n } from "vue-i18n";
const tenantsStore = useTenantsStore();
const authStore = useAuthStore();
const { addToast } = useToast();
const { t } = useI18n();

const selectedFile = ref(null);
const loading = ref(false);

const startUrl = ref("");
const crawlSinglePageOnly = ref(false);
const excludedUrls = ref("");

const sourceToDelete = ref(null);
const showConfirmationModal = ref(false);

const crawlingJobs = ref([]);

const isUrlValid = computed(() => {
  if (!startUrl.value) return true;
  let urlString = startUrl.value.trim();
  if (!urlString.startsWith('http://') && !urlString.startsWith('https://')) {
    urlString = 'https://' + urlString;
  }
  try {
    const url = new URL(urlString);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch (_) {
    return false;
  }
});

const urlSources = computed(() => {
  if (tenantsStore.currentTenant && tenantsStore.currentTenant.tenant_sources) {
    return tenantsStore.currentTenant.tenant_sources.filter(
      (s) => s.source_type === "URL"
    );
  }
  return [];
});

const fileSources = computed(() => {
  if (tenantsStore.currentTenant && tenantsStore.currentTenant.tenant_sources) {
    return tenantsStore.currentTenant.tenant_sources.filter(
      (s) => s.source_type === "FILE"
    );
  }
  return [];
});



const startCrawl = async () => {
  if (!startUrl.value.trim() || !tenantsStore.currentTenant) return;
  loading.value = true;

  let finalUrl = startUrl.value.trim();
  if (!finalUrl.startsWith('http://') && !finalUrl.startsWith('https://')) {
    finalUrl = 'https://' + finalUrl;
  }

  const payload = {
    url: finalUrl,
    single_page_only: crawlSinglePageOnly.value,
    excluded_urls: crawlSinglePageOnly.value
      ? []
      : excludedUrls.value.split("\n").filter((url) => url.trim() !== ""),
  };

  try {
    await apiClient.post(
      `/tenants/${tenantsStore.currentTenant.id}/sources/discover`,
      payload
    );
    addToast(t("tenant.sources.actions.crawlStarted"), "success");
    startUrl.value = "";
    crawlSinglePageOnly.value = false;
    excludedUrls.value = "";
    await fetchCrawlingJobs(); // Refresh the jobs list
  } catch (error) {
    addToast(
      `${t("tenant.sources.actions.crawlFailed")} ${
        error.response?.data?.error || "Unknown error"
      }`,
      "error"
    );
  } finally {
    loading.value = false;
  }
};

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0];
};

const handleUpload = async () => {
  if (!selectedFile.value || !tenantsStore.currentTenant) return;
  loading.value = true;
  const formData = new FormData();
  formData.append("file", selectedFile.value);
  try {
    await apiClient.post(
      `/tenants/${tenantsStore.currentTenant.id}/sources/upload`,
      formData
    );
    await tenantsStore.refetch(tenantsStore.currentTenant.id);
    selectedFile.value = null;
    document.getElementById("file-upload").value = "";
    addToast(t("tenant.sources.actions.uploadSuccess"), "success");
  } catch (error) {
    let errorMessage = "Unknown error";
    if (error.response) {
      console.error("Error response data:", error.response.data);
      if (typeof error.response.data === "string") {
        errorMessage = error.response.data;
      } else if (error.response.data && error.response.data.error) {
        errorMessage = error.response.data.error;
      } else {
        errorMessage = `Server error: ${error.response.status}`;
      }
    } else if (error.request) {
      errorMessage = "No response from server. Check network connection.";
    } else {
      errorMessage = error.message;
    }
    addToast(
      `${t("tenant.sources.actions.uploadFailed")} ${errorMessage}`,
      "error"
    );
  } finally {
    loading.value = false;
  }
};

const confirmDelete = (source) => {
  sourceToDelete.value = source;
  showConfirmationModal.value = true;
};

const cancelDelete = () => {
  sourceToDelete.value = null;
  showConfirmationModal.value = false;
};

const handleDelete = async () => {
  if (!tenantsStore.currentTenant || !sourceToDelete.value) return;
  const sourceIdToDelete = sourceToDelete.value.id;

  const originalSources = [...tenantsStore.currentTenant.tenant_sources];

  // Optimistic UI update
  const sourceIndex = tenantsStore.currentTenant.tenant_sources.findIndex(
    (s) => s.id === sourceIdToDelete
  );
  if (sourceIndex > -1) {
    tenantsStore.currentTenant.tenant_sources.splice(sourceIndex, 1);
  }

  try {
    await apiClient.delete(
      `/tenants/${tenantsStore.currentTenant.id}/sources/${sourceIdToDelete}`
    );
    addToast(t("tenant.sources.actions.deleteSuccess"), "success");
    // After successful deletion, we can choose to refetch for consistency or trust the optimistic update.
    // For now, we'll rely on the optimistic update for speed.
    // await tenantsStore.refetch(tenantsStore.currentTenant.id);
  } catch (error) {
    // If the delete fails, revert the UI change
    tenantsStore.currentTenant.tenant_sources = originalSources;
    addToast(
      `${t("tenant.sources.actions.deleteFailed")} ${
        error.response?.data?.error || "Unknown error"
      }`,
      "error"
    );
  } finally {
    cancelDelete();
  }
};

const handleJobCompletion = async (jobId) => {
  addToast(t("tenant.sources.actions.crawlCompleted"), "success");
  await tenantsStore.refetch(tenantsStore.currentTenant.id);
  await fetchCrawlingJobs();
};

const fetchCrawlingJobs = async () => {
  if (!tenantsStore.currentTenant) return;
  try {
    const response = await apiClient.get(
      `/tenants/${tenantsStore.currentTenant.id}/crawling_jobs`
    );
    crawlingJobs.value = response.data;
  } catch (error) {
    addToast(t("tenant.sources.actions.fetchFailed"), "error");
    console.error("Failed to fetch crawling jobs:", error);
  }
};

watch(
  () => tenantsStore.currentTenant,
  (newTenant) => {
    if (newTenant) {
      fetchCrawlingJobs();
    } else {
      crawlingJobs.value = [];
    }
  },
  { immediate: true }
);
</script>
