<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
    <!-- Left side: Add new sources -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg space-y-6">
      <h3 class="text-xl font-bold text-orange-400">Add New Source</h3>

      <!-- File Upload -->
      <div>
        <label for="file-upload" class="block text-sm font-medium text-gray-300 mb-2">Upload File</label>
        <input id="file-upload" type="file" @change="handleFileSelect" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100" />
        <button @click="handleUpload" :disabled="!selectedFile || loading" class="mt-2 w-full bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ loading ? 'Uploading...' : 'Upload File' }}
        </button>
      </div>

      <!-- URL Crawl -->
      <div>
        <label for="url-input" class="block text-sm font-medium text-gray-300 mb-2">Crawl Website</label>
        <input v-model="startUrl" id="url-input" type="text" placeholder="Enter a single domain to crawl (e.g., example.com)"
          class="w-full p-3 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500">
        <button @click="discoverLinks" :disabled="!startUrl.trim() || loading" class="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
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
        <button @click="handleFinalCrawl" :disabled="!selectedDepth || loading" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ loading ? 'Crawling...' : `Crawl ${getTotalLinks(selectedDepth)} Pages` }}
        </button>
      </div>
    </div>

    <!-- Right side: List of existing sources -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h3 class="text-xl font-bold text-orange-400 mb-4">Existing Sources</h3>
      <div v-if="tenantsStore.currentTenant && tenantsStore.currentTenant.tenant_sources.length > 0" class="space-y-4 max-h-96 overflow-y-auto">

        <!-- URL Sources Accordion -->
        <details class="bg-gray-700 rounded-lg" open>
          <summary class="cursor-pointer font-semibold p-4">
            Crawled URLs ({{ urlSources.length }})
          </summary>
          <div class="border-t border-gray-600 p-4 space-y-2">
            <div v-for="source in urlSources" :key="source.id" class="bg-gray-600 p-3 rounded-lg flex justify-between items-center">
              <div>
                <p class="font-semibold truncate" :title="source.source_location">{{ source.source_location }}</p>
                <p class="text-xs text-gray-400">Status: {{ source.status }}</p>
              </div>
              <button @click="handleDelete(source.id)" class="text-red-500 hover:text-red-400 text-2xl leading-none">&times;</button>
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
              <button @click="handleDelete(source.id)" class="text-red-500 hover:text-red-400 text-2xl leading-none">&times;</button>
            </div>
             <p v-if="fileSources.length === 0" class="text-gray-500 text-sm">No files have been uploaded yet.</p>
          </div>
        </details>

      </div>
      <p v-else class="text-gray-500">No sources added yet.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import axios from 'axios'
import { useAuthStore } from '../../stores/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
const tenantsStore = useTenantsStore()
const authStore = useAuthStore()

const selectedFile = ref(null)
const loading = ref(false)

// New state for recursive crawl
const startUrl = ref('')
const discoveryResults = ref([])
const selectedDepth = ref(0)

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
            selectedDepth.value = discoveryResults.value.length; // Default to max depth
        }
    } catch (error) {
        console.error('Link discovery failed:', error);
        alert(`Link discovery failed: ${error.response?.data?.error || 'Unknown error'}`);
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
        await tenantsStore.fetchTenant(tenantsStore.currentTenant.id); // Refresh data
        startUrl.value = '';
        discoveryResults.value = [];
        selectedDepth.value = 0;
    } catch (error) {
        console.error('URL crawling failed:', error);
        alert(`URL crawling failed: ${error.response?.data?.error || 'Unknown error'}`);
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
    await tenantsStore.fetchTenant(tenantsStore.currentTenant.id) // Refresh data
    selectedFile.value = null
    document.getElementById('file-upload').value = ''
  } catch (error) {
    console.error('File upload failed:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (sourceId) => {
  if (!tenantsStore.currentTenant) return
  if (confirm('Are you sure you want to delete this source? This might affect your chatbot\'s knowledge.')) {
    try {
        await axios.delete(`${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/${sourceId}`, { headers: getAuthHeaders() })
        await tenantsStore.fetchTenant(tenantsStore.currentTenant.id) // Refresh data
    } catch (error) {
        console.error('Failed to delete source:', error)
    }
  }
}
</script>
