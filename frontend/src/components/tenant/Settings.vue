<template>
  <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
    <form @submit.prevent="handleUpdate" class="space-y-6">
      <div>
        <label for="name" class="block text-sm font-medium text-gray-300">Tenant Name</label>
        <input v-model="formData.name" type="text" id="name" required
          class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
      </div>
      <div>
        <label for="intro_message" class="block text-sm font-medium text-gray-300">Intro Message</label>
        <textarea v-model="formData.intro_message" id="intro_message" rows="3"
          class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"></textarea>
      </div>
      <div>
        <label for="system_persona" class="block text-sm font-medium text-gray-300">System Persona</label>
        <textarea v-model="formData.system_persona" id="system_persona" rows="5"
          class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"></textarea>
      </div>
      <div>
        <label for="rag_prompt_template" class="block text-sm font-medium text-gray-300">RAG Prompt Template</label>
        <textarea v-model="formData.rag_prompt_template" id="rag_prompt_template" rows="8"
          class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"></textarea>
      </div>
      <div class="flex justify-end">
        <button type="submit" :disabled="tenantsStore.loading"
          class="bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ tenantsStore.loading ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTenantsStore } from '../../stores/tenants'

const tenantsStore = useTenantsStore()
const formData = ref({
  name: '',
  intro_message: '',
  system_persona: '',
  rag_prompt_template: ''
})

watch(() => tenantsStore.currentTenant, (newTenant) => {
  if (newTenant) {
    formData.value = {
      name: newTenant.name,
      intro_message: newTenant.intro_message,
      system_persona: newTenant.system_persona,
      rag_prompt_template: newTenant.rag_prompt_template
    }
  }
}, { immediate: true })

const handleUpdate = async () => {
  if (tenantsStore.currentTenant) {
    await tenantsStore.updateTenant(tenantsStore.currentTenant.id, formData.value)
    // Optionally, show a success message
  }
}
</script>
