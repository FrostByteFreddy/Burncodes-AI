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
        <label for="url-input" class="block text-sm font-medium text-gray-300 mb-2">Crawl URLs</label>
        <textarea v-model="urlsToCrawl" id="url-input" rows="4" placeholder="Enter one URL per line"
          class="w-full p-3 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"></textarea>
        <button @click="handleCrawl" :disabled="!urlsToCrawl.trim() || loading" class="mt-2 w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ loading ? 'Crawling...' : 'Crawl URLs' }}
        </button>
      </div>
    </div>

    <!-- Right side: List of existing sources -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h3 class="text-xl font-bold text-orange-400 mb-4">Existing Sources</h3>
      <div v-if="tenantsStore.currentTenant && tenantsStore.currentTenant.tenant_sources.length > 0" class="space-y-3 max-h-96 overflow-y-auto">
        <div v-for="source in tenantsStore.currentTenant.tenant_sources" :key="source.id" class="bg-gray-700 p-3 rounded-lg flex justify-between items-center">
          <div>
            <p class="font-semibold truncate" :title="source.source_location">{{ source.source_location }}</p>
            <p class="text-xs text-gray-400">Type: {{ source.source_type }} | Status: {{ source.status }}</p>
          </div>
          <button @click="handleDelete(source.id)" class="text-red-500 hover:text-red-400">&times;</button>
        </div>
      </div>
      <p v-else class="text-gray-500">No sources added yet.</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
const tenantsStore = useTenantsStore()
const selectedFile = ref(null)
const urlsToCrawl = ref('')
const loading = ref(false)

import { useAuthStore } from '../../stores/auth'
const authStore = useAuthStore()

const getAuthHeaders = () => {
    if (!authStore.session?.access_token) {
        throw new Error('User is not authenticated.')
    }
    return { Authorization: `Bearer ${authStore.session.access_token}` }
}

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

const handleCrawl = async () => {
    if (!urlsToCrawl.value.trim() || !tenantsStore.currentTenant) return
    loading.value = true
    const urls = urlsToCrawl.value.split('\n').filter(url => url.trim() !== '')
    try {
        await axios.post(`${API_BASE_URL}/tenants/${tenantsStore.currentTenant.id}/sources/crawl`, { urls }, { headers: getAuthHeaders() })
        await tenantsStore.fetchTenant(tenantsStore.currentTenant.id) // Refresh data
        urlsToCrawl.value = ''
    } catch (error) {
        console.error('URL crawling failed:', error)
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
