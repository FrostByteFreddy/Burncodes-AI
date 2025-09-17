<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
    <!-- Left side: Add new sources -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg space-y-6">
      <h3 class="text-xl font-bold text-brand-white">Add New Source</h3>

      <!-- File Upload -->
      <div>
        <label for="file-upload" class="block text-sm font-medium text-gray-300 mb-2">Upload File</label>
        <input id="file-upload" type="file" @change="handleFileSelect" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-white hover:file:bg-gray-600" />
        <button @click="handleUpload" :disabled="!selectedFile || loading" class="mt-2 w-full bg-black border border-white hover:bg-gray-900 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ loading ? 'Uploading...' : 'Upload File' }}
        </button>
      </div>

      <!-- URL Crawl -->
      <div>
        <label for="url-input" class="block text-sm font-medium text-gray-300 mb-2 mt-5">Crawl Website</label>
        <input v-model="startUrl" id="url-input" type="text" placeholder="https://example.com"
          class="w-full p-3 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-white"
          :class="{'border-red-500': !isUrlValid && startUrl}"
          aria-invalid="!isUrlValid && startUrl"
          aria-describedby="url-error"
        >
        <p v-if="!isUrlValid && startUrl" id="url-error" class="text-red-400 text-sm mt-1">Please enter a valid URL (e.g., https://example.com).</p>
        <button @click="discoverLinks" :disabled="!startUrl.trim() || loading || !isUrlValid" class="mt-2 w-full bg-black border border-white hover:bg-gray-900 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ loading ? 'Discovering...' : 'Discover Links' }}
        </button>
      </div>

      <!-- Discovery Results -->
      <div v-if="discoveryResults.length > 0" class="space-y-4">
        <h4 class="text-lg font-semibold">Discovery Results</h4>
        <div class="bg-gray-700 p-4 rounded-lg">
          <div v-for="result in discoveryResults" :key="result.depth" class="flex justify-between items-center">
            <span>Depth {{ result.depth }}:</span>
            <span>{{ result.count }} links found</span>
          </div>
        </div>
        <div>
          <label for="depth-select" class="block text-sm font-medium text-gray-300 mb-2">Select crawl depth</label>
          <select v-model.number="selectedDepth" id="depth-select" class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg">
            <option v-for="result in discoveryResults" :key="result.depth" :value="result.depth">
              Up to Depth {{ result.depth }} ({{ getTotalLinks(result.depth) }} total pages)
            </option>
          </select>
        </div>
        <button @click="handleFinalCrawl" :disabled="!selectedDepth || loading" class="w-full bg-black border border-white hover:bg-gray-900 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ loading ? 'Crawling...' : `Crawl ${getTotalLinks(selectedDepth)} Pages` }}
        </button>
      </div>
    </div>

    <!-- Right side: List of existing sources -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h3 class="text-xl font-bold text-brand-white mb-4">Existing Sources</h3>

      <!-- Loading Skeleton -->
      <div v-if="tenantsStore.loading" class="space-y-4">
        <div v-for="n in 3" :key="n" class="h-16 bg-gray-700 rounded-lg animate-pulse"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!tenantsStore.currentTenant || tenantsStore.currentTenant.tenant_sources.length === 0" class="text-center p-8 rounded-lg bg-gray-700">
        <h4 class="text-xl font-semibold">No sources yet</h4>
        <p class="text-gray-400 mt-2">Add a source to start building your chatbot's knowledge base.</p>
      </div>

      <!-- Existing Sources List -->
      <div v-else class="space-y-4 max-h-96 overflow-y-auto">
        <!-- URL Sources Accordion -->
        <details class="bg-gray-700 rounded-lg">
          <summary class="cursor-pointer font-semibold p-4">
            Crawled URLs ({{ urlSources.length }})
          </summary>
          <div class="border-t border-gray-600 p-4 space-y-2">
            <div v-for="source in urlSources" :key="source.id" class="bg-gray-600 p-3 rounded-lg flex justify-between items-center">
              <div>
                <p class="font-semibold truncate" :title="source.source_location">{{ source.source_location }}</p>
                <p class="text-xs text-gray-400">Status: {{ source.status }}</p>
              </div>
              <button @click="confirmDelete(source)" class="text-red-500 hover:text-red-400 font-semibold text-xl">&times;</button>
            </div>
            <p v-if="urlSources.length === 0" class="text-gray-500 text-sm">No URLs have been crawled yet.</p>
          </div>
        </details>

        <!-- File Sources Accordion -->
        <details class="bg-gray-700 rounded-lg" open>
          <summary class="cursor-pointer font-semibold p-4">
            Uploaded Files ({{ fileSources.length }})
          </summary>
          <div class="border-t border-gray-600 p-4 space-y-2">
            <div v-for="source in fileSources" :key="source.id" class="bg-gray-600 p-3 rounded-lg flex justify-between items-center">
              <div>
                <p class="font-semibold truncate" :title="source.source_location">{{ source.source_location }}</p>
                <p class="text-xs text-gray-400">Status: {{ source.status }}</p>
              </div>
              <button @click="confirmDelete(source)" class="text-red-500 hover:text-red-400 font-semibold text-xl">&times;</button>
            </div>
             <p v-if="fileSources.length === 0" class="text-gray-500 text-sm">No files have been uploaded yet.</p>
          </div>
        </details>
      </div>
    </div>

    <ConfirmationModal
      :show="showConfirmationModal"
      title="Delete Source"
      :message="`Are you sure you want to delete the source '${sourceToDelete?.source_location}'?`"
      confirmButtonText="Delete"
      @confirm="handleDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import { useAuthStore } from '../../stores/auth'
import { useToast } from '../../composables/useToast'
import ConfirmationModal from '../ConfirmationModal.vue'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
const tenantsStore = useTenantsStore()
const authStore = useAuthStore()
const { addToast } = useToast()

const selectedFile = ref(null)
const loading = ref(false)

const startUrl = ref('')
const discoveryResults = ref([])
const selectedDepth = ref(0)

const sourceToDelete = ref(null)
const showConfirmationModal = ref(false)

const isUrlValid = computed(() => {
  if (!startUrl.value) return true;
  try {
    const url = new URL(startUrl.value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch (_) {
    return false;
  }
});

const urlSources = computed(() => {
  if (tenantsStore.currentTenant && tenantsStore.currentTenant.tenant_sources) {
    return tenantsStore.currentTenant.tenant_sources.filter(s => s.source_type === 'URL')
  }
  return []
})

const fileSources = computed(() => {
  if (tenantsStore.currentTenant && tenantsStore.currentTenant.tenant_sources) {
    return tenantsStore.currentTenant.tenant_sources.filter(s => s.source_type === 'FILE')
  }
  return []
})

const getAuthHeaders = () => {
    if (!authStore.session?.access_token) {
        throw new Error('User is not authenticated.')
    }
    return { Authorization: `Bearer ${authStore.session.access_token}` }
}

const getTotalLinks = (depth) => {
  return discoveryResults.value
    .slice(0, depth)
    .reduce((total, result) => total + result.count, 0);
};

const discoverLinks = async () => {
    if (!startUrl.value.trim() || !tenantsStore.currentTenant) return;
    loading.value = true;
    discoveryResults.value = [];
    selectedDepth.value = 0;
    try {
        const response = await axios.post(`${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/discover`, { url: startUrl.value }, { headers: getAuthHeaders() });
        discoveryResults.value = response.data;
        if (discoveryResults.value.length > 0) {
            selectedDepth.value = discoveryResults.value.length;
        }
        addToast('Link discovery successful!', 'success');
    } catch (error) {
        addToast(`Link discovery failed: ${error.response?.data?.error || 'Unknown error'}`, 'error');
    } finally {
        loading.value = false;
    }
};

const handleFinalCrawl = async () => {
    if (!selectedDepth.value || !tenantsStore.currentTenant) return;
    loading.value = true;

    const urlsToCrawl = discoveryResults.value
        .slice(0, selectedDepth.value)
        .flatMap(result => result.links);

    try {
        await axios.post(`${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/crawl`, { urls: urlsToCrawl }, { headers: getAuthHeaders() });
        await tenantsStore.fetchTenant(tenantsStore.currentTenant.id);
        startUrl.value = '';
        discoveryResults.value = [];
        selectedDepth.value = 0;
        addToast('Crawling initiated successfully!', 'success');
    } catch (error) {
        addToast(`URL crawling failed: ${error.response?.data?.error || 'Unknown error'}`, 'error');
    } finally {
        loading.value = false;
    }
};

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

const handleUpload = async () => {
  if (!selectedFile.value || !tenantsStore.currentTenant) return
  loading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  try {
    await axios.post(`${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/upload`, formData, { headers: getAuthHeaders() })
    await tenantsStore.fetchTenant(tenantsStore.currentTenant.id)
    selectedFile.value = null
    document.getElementById('file-upload').value = ''
    addToast('File uploaded successfully!', 'success');
  } catch (error) {
    let errorMessage = 'Unknown error';
    if (error.response) {
      console.error('Error response data:', error.response.data);
      if (typeof error.response.data === 'string') {
        errorMessage = error.response.data;
      } else if (error.response.data && error.response.data.error) {
        errorMessage = error.response.data.error;
      } else {
        errorMessage = `Server error: ${error.response.status}`;
      }
    } else if (error.request) {
      errorMessage = 'No response from server. Check network connection.';
    } else {
      errorMessage = error.message;
    }
    addToast(`File upload failed: ${errorMessage}`, 'error');
  } finally {
    loading.value = false
  }
}

const confirmDelete = (source) => {
  sourceToDelete.value = source;
  showConfirmationModal.value = true;
};

const cancelDelete = () => {
  sourceToDelete.value = null;
  showConfirmationModal.value = false;
};

const handleDelete = async () => {
  if (!tenantsStore.currentTenant || !sourceToDelete.value) return
  try {
      await axios.delete(`${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/${sourceToDelete.value.id}`, { headers: getAuthHeaders() })
      await tenantsStore.fetchTenant(tenantsStore.currentTenant.id)
      addToast('Source deleted successfully!', 'success');
  } catch (error) {
      addToast(`Failed to delete source: ${error.response?.data?.error || 'Unknown error'}`, 'error');
  } finally {
    cancelDelete();
  }
}
</script>
