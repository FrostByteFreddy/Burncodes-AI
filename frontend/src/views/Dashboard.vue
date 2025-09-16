<template>
  <div class="container mx-auto p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold">My Tenants</h1>
      <button @click="showCreateModal = true"
        class="bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white font-bold py-2 px-4 rounded-lg">
        Create New Tenant
      </button>
    </div>

    <div v-if="tenantsStore.loading" class="text-center">
      <p>Loading tenants...</p>
    </div>
    <div v-else-if="tenantsStore.error" class="text-center text-red-400">
      <p>Error: {{ tenantsStore.error }}</p>
    </div>
    <div v-else-if="tenantsStore.tenants.length === 0"
      class="text-center bg-gray-800 p-8 rounded-lg">
      <h2 class="text-2xl font-semibold mb-2">No tenants found</h2>
      <p class="text-gray-400">Get started by creating your first tenant chatbot.</p>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="tenant in tenantsStore.tenants" :key="tenant.id"
        class="bg-gray-800 p-6 rounded-lg shadow-lg flex flex-col justify-between">
        <div>
          <h2 class="text-xl font-bold mb-2 truncate">{{ tenant.name }}</h2>
          <p class="text-gray-400 text-sm mb-4 h-10 overflow-hidden">{{ tenant.intro_message }}</p>
        </div>
        <div class="flex justify-between items-center mt-4">
          <router-link :to="{ name: 'Tenant', params: { tenantId: tenant.id } }"
            class="text-orange-400 hover:underline">Manage</router-link>
          <div class="flex space-x-2">
            <a :href="`/chat/${tenant.id}`" target="_blank"
              class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold py-1 px-3 rounded">Test</a>
            <button @click="handleDelete(tenant.id)"
              class="bg-red-600 hover:bg-red-700 text-white text-sm font-bold py-1 px-3 rounded">Delete</button>
          </div>
        </div>
      </div>
    </div>

    <CreateTenantModal
      :show="showCreateModal"
      @close="showCreateModal = false"
      @create="handleCreateTenant"
    />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useAuthStore } from '../stores/auth'
import CreateTenantModal from '../components/CreateTenantModal.vue'

const tenantsStore = useTenantsStore()
const authStore = useAuthStore()
const showCreateModal = ref(false)

onMounted(() => {
  if (authStore.user) {
    tenantsStore.fetchTenants()
  }
})

watch(() => authStore.user, (newUser) => {
  if (newUser) {
    tenantsStore.fetchTenants()
  }
})

const handleCreateTenant = async (tenantData) => {
  try {
    await tenantsStore.createTenant(tenantData)
    showCreateModal.value = false
  } catch (error) {
    console.error("Failed to create tenant:", error)
    // Optionally, show an error message to the user
  }
}

const handleDelete = async (id) => {
  if (confirm('Are you sure you want to delete this tenant and all its data? This cannot be undone.')) {
    await tenantsStore.deleteTenant(id)
  }
}
</script>
