```
<template>
  <div class="card">
    <div
      class="inline-flex p-1 space-x-1 bg-primary/10 rounded-full mb-6 w-fit"
    >
      <a
        class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
        :class="{
          '!bg-primary text-primary-content shadow': activeTab === 'website',
          'btn-ghost text-base-content': activeTab !== 'website',
        }"
        @click="activeTab = 'website'"
      >
        <font-awesome-icon :icon="['fas', 'globe']" />
        <span>{{ $t("tenant.sources.tabs.website") }}</span>
      </a>
      <a
        class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
        :class="{
          '!bg-primary text-primary-content shadow': activeTab === 'files',
          'btn-ghost text-base-content': activeTab !== 'files',
        }"
        @click="activeTab = 'files'"
      >
        <font-awesome-icon :icon="['fas', 'file-lines']" />
        <span>{{ $t("tenant.sources.tabs.files") }}</span>
      </a>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <!-- Website Tab -->
      <div v-if="activeTab === 'website'" class="contents">
        <!-- Left side: Add new website source -->
        <div class="card space-y-6">
          <h3 class="text-xl font-bold text-base-content flex items-center">
            <font-awesome-icon
              :icon="['fas', 'plus-circle']"
              class="mr-3 text-primary"
            />
            {{ $t("tenant.sources.addNew") }}
          </h3>

          <!-- URL Crawl -->
          <div>
            <label
              for="url-input"
              class="block text-sm font-medium text-base-content mb-2"
              >{{ $t("tenant.sources.crawlWebsite") }}</label
            >
            <input
              v-model="startUrl"
              id="url-input"
              type="text"
              placeholder="https://example.com"
              class="w-full p-3 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              :class="{ 'border-error': !isUrlValid && startUrl }"
              aria-invalid="!isUrlValid && startUrl"
              aria-describedby="url-error"
            />
            <p
              v-if="!isUrlValid && startUrl"
              id="url-error"
              class="text-error text-sm mt-1"
            >
              {{ $t("tenant.sources.invalidUrl") }}
            </p>
            <div class="form-control mt-4">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  v-model="crawlSinglePageOnly"
                  class="h-4 w-4 rounded border-base-300 text-primary focus:ring-primary"
                  id="single_crawl_only"
                />
                <label for="single_crawl_only" class="ml-2 block text-sm"
                  >Crawl only this page</label
                >
              </div>
            </div>

            <div v-if="!crawlSinglePageOnly" class="mt-4">
              <label
                for="excluded-urls-input"
                class="block text-sm font-medium text-base-content mb-2"
                >{{ $t("tenant.sources.excludeUrls") }}</label
              >
              <textarea
                v-model="excludedUrls"
                id="excluded-urls-input"
                :placeholder="$t('tenant.sources.excludePlaceholder')"
                rows="3"
                class="w-full p-3 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              ></textarea>
            </div>

            <button
              @click="startCrawl"
              :disabled="!startUrl.trim() || loading || !isUrlValid"
              class="mt-4 w-full btn btn-primary"
            >
              <font-awesome-icon :icon="['fas', 'globe']" class="mr-2" />
              {{
                loading
                  ? $t("tenant.sources.crawling")
                  : $t("tenant.sources.crawlWebsite")
              }}
            </button>
          </div>
        </div>

        <!-- Right side: List of existing website sources -->
        <div class="card">
          <!-- Crawling Activity -->
          <div class="mb-8">
            <h3
              class="text-xl font-bold text-base-content mb-4 flex items-center"
            >
              <font-awesome-icon
                :icon="['fas', 'person-digging']"
                class="mr-3 text-primary"
              />
              {{ $t("tenant.sources.activity.title") }}
            </h3>
            <div
              v-if="crawlingJobs.length === 0"
              class="text-center p-8 rounded-lg bg-base-200"
            >
              <h4 class="text-xl font-semibold">
                {{ $t("tenant.sources.activity.noActivity") }}
              </h4>
              <p class="text-base-content/70 mt-2">
                {{ $t("tenant.sources.activity.instruction") }}
              </p>
            </div>
            <div v-else class="space-y-4 max-h-60 overflow-y-auto">
              <div
                v-for="job in crawlingJobs"
                :key="job.id"
                class="bg-base-200 p-4 rounded-lg"
              >
                <p class="font-semibold truncate" :title="job.start_url">
                  {{ job.start_url }}
                </p>
                <div class="flex justify-between items-center mt-2">
                  <p class="text-xs text-base-content/70">
                    {{ $t("tenant.sources.activity.status") }}:
                    <span
                      class="font-bold"
                      :class="{
                        'text-success': job.status === 'COMPLETED',
                        'text-warning': job.status === 'IN_PROGRESS',
                      }"
                      >{{ job.status }}</span
                    >
                  </p>
                  <p class="text-xs text-base-content/70">
                    {{ new Date(job.created_at).toLocaleString() }}
                  </p>
                </div>
                <CrawlingJobProgress
                  :job="job"
                  :tenantId="tenantsStore.currentTenant.id"
                  @job-completed="handleJobCompletion"
                />
              </div>
            </div>
          </div>

          <h3
            class="text-xl font-bold text-base-content mb-4 flex items-center"
          >
            <font-awesome-icon
              :icon="['fas', 'list-alt']"
              class="mr-3 text-primary"
            />
            {{ $t("tenant.sources.existing.title") }}
          </h3>

          <!-- Loading Skeleton -->
          <div v-if="tenantsStore.loading" class="space-y-4">
            <div
              v-for="n in 3"
              :key="n"
              class="h-16 bg-base-200 rounded-lg animate-pulse"
            ></div>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="urlSources.length === 0"
            class="text-center p-8 rounded-lg bg-base-200"
          >
            <h4 class="text-xl font-semibold">
              {{ $t("tenant.sources.existing.noCrawledUrls") }}
            </h4>
            <p class="text-base-content/70 mt-2">
              {{ $t("tenant.sources.existing.instruction") }}
            </p>
          </div>

          <!-- Existing Sources List -->
          <div v-else class="space-y-4 max-h-96 overflow-y-auto">
            <div
              v-for="source in urlSources"
              :key="source.id"
              class="bg-base-200 p-4 rounded-lg flex justify-between items-center"
            >
              <div>
                <p
                  class="font-semibold truncate max-w-xs"
                  :title="source.source_location"
                >
                  {{ source.source_location }}
                </p>
                <div class="flex gap-4 mt-1">
                  <p class="text-xs text-base-content/70">
                    {{ $t("tenant.sources.activity.status") }}:
                    {{ source.status }}
                  </p>
                  <p class="text-xs text-base-content/70">
                    {{ $t("tenant.sources.cost") }}: CHF
                    {{ (source.cost_chf || 0).toFixed(4) }}
                  </p>
                </div>
              </div>
              <button
                @click="confirmDelete(source)"
                class="btn btn-sm text-error hover:bg-error/10"
              >
                <font-awesome-icon :icon="['fas', 'trash']" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Files Tab -->
      <div v-if="activeTab === 'files'" class="contents">
        <!-- Left side: Add new file source -->
        <div class="card space-y-6">
          <h3 class="text-xl font-bold text-base-content flex items-center">
            <font-awesome-icon
              :icon="['fas', 'plus-circle']"
              class="mr-3 text-primary"
            />
            {{ $t("tenant.sources.addNew") }}
          </h3>

          <!-- File Upload -->
          <div>
            <label
              for="file-upload"
              class="block text-sm font-medium text-base-content mb-2"
              >{{ $t("tenant.sources.uploadFile") }}</label
            >
            <input
              id="file-upload"
              type="file"
              @change="handleFileSelect"
              class="block w-full text-sm text-base-content/70 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
            />
            <button
              @click="handleUpload"
              :disabled="!selectedFile || loading"
              class="mt-2 w-full btn btn-primary"
            >
              <font-awesome-icon :icon="['fas', 'upload']" class="mr-2" />
              {{
                loading
                  ? $t("tenant.sources.uploading")
                  : $t("tenant.sources.uploadFile")
              }}
            </button>
          </div>
        </div>

        <!-- Right side: List of existing file sources -->
        <div class="card">
          <h3
            class="text-xl font-bold text-base-content mb-4 flex items-center"
          >
            <font-awesome-icon
              :icon="['fas', 'list-alt']"
              class="mr-3 text-primary"
            />
            {{ $t("tenant.sources.existing.title") }}
          </h3>

          <!-- Loading Skeleton -->
          <div v-if="tenantsStore.loading" class="space-y-4">
            <div
              v-for="n in 3"
              :key="n"
              class="h-16 bg-base-200 rounded-lg animate-pulse"
            ></div>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="fileSources.length === 0"
            class="text-center p-8 rounded-lg bg-base-200"
          >
            <h4 class="text-xl font-semibold">
              {{ $t("tenant.sources.existing.noUploadedFiles") }}
            </h4>
            <p class="text-base-content/70 mt-2">
              {{ $t("tenant.sources.existing.instruction") }}
            </p>
          </div>

          <!-- Existing Sources List -->
          <div v-else class="space-y-4 max-h-96 overflow-y-auto">
            <div
              v-for="source in fileSources"
              :key="source.id"
              class="bg-base-200 p-4 rounded-lg flex justify-between items-center"
            >
              <div>
                <p
                  class="font-semibold truncate max-w-xs"
                  :title="source.source_location"
                >
                  {{ getFileName(source.source_location) }}
                </p>
                <div class="flex gap-4 mt-1">
                  <p class="text-xs text-base-content/70">
                    {{ $t("tenant.sources.activity.status") }}:
                    {{ source.status }}
                  </p>
                  <p class="text-xs text-base-content/70">
                    {{ $t("tenant.sources.cost") }}: CHF
                    {{ (source.cost_chf || 0).toFixed(4) }}
                  </p>
                </div>
              </div>
              <button
                @click="confirmDelete(source)"
                class="btn btn-sm text-error hover:bg-error/10"
              >
                <font-awesome-icon :icon="['fas', 'trash']" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ConfirmationModal
      :show="showConfirmationModal"
      :title="$t('tenant.sources.deleteModal.title')"
      :message="
        $t('tenant.sources.deleteModal.message', {
          source: sourceToDelete?.source_location,
        })
      "
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
import axios from "axios";

import { useI18n } from "vue-i18n";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";
const tenantsStore = useTenantsStore();
const authStore = useAuthStore();
const { addToast } = useToast();
const { t } = useI18n();

const activeTab = ref("website");
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
  try {
    const url = new URL(startUrl.value);
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

const getAuthHeaders = () => {
  if (!authStore.session?.access_token) {
    throw new Error("User is not authenticated.");
  }
  return { Authorization: `Bearer ${authStore.session.access_token}` };
};

const startCrawl = async () => {
  if (!startUrl.value.trim() || !tenantsStore.currentTenant) return;
  loading.value = true;

  const payload = {
    url: startUrl.value,
    single_page_only: crawlSinglePageOnly.value,
    excluded_urls: crawlSinglePageOnly.value
      ? []
      : excludedUrls.value.split("\n").filter((url) => url.trim() !== ""),
  };

  try {
    await axios.post(
      `${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/discover`,
      payload,
      { headers: getAuthHeaders() }
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
    await axios.post(
      `${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/upload`,
      formData,
      { headers: getAuthHeaders() }
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
    await axios.delete(
      `${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/${sourceIdToDelete}`,
      { headers: getAuthHeaders() }
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
    const response = await axios.get(
      `${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/crawling_jobs`,
      { headers: getAuthHeaders() }
    );
    crawlingJobs.value = response.data;
  } catch (error) {
    addToast(t("tenant.sources.actions.fetchFailed"), "error");
    console.error("Failed to fetch crawling jobs:", error);
  }
};

onMounted(() => {
  fetchCrawlingJobs();
});

watch(
  () => tenantsStore.currentTenant,
  (newTenant) => {
    if (newTenant) {
      fetchCrawlingJobs();
    }
  }
);

const getFileName = (path) => {
  if (!path) return "";
  const parts = path.split("/");
  return parts[parts.length - 1];
};
</script>
