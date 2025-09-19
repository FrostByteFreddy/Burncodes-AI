<template>
  <div class="container mx-auto p-6">
    <div v-if="tenantsStore.currentTenant" class="mb-8">
      <h1 class="text-3xl font-bold">{{ tenantsStore.currentTenant.name }}</h1>
      <p class="text-gray-400">Manage your tenant settings, sources, and advanced configurations.</p>
    </div>
    <div v-else-if="tenantsStore.loading" class="text-center p-10">
      <p>Loading tenant...</p>
    </div>
    <div v-else class="text-center p-10 text-red-400">
      <p>Could not load tenant data. It might not exist or you may not have permission to view it.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
      <!-- Main Content -->
      <main class="md:col-span-4">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useRoute } from 'vue-router'

const tenantsStore = useTenantsStore()
const route = useRoute()

onMounted(() => {
  // Fetch tenant data if it's not already loaded or if the ID is different
  if (!tenantsStore.currentTenant || tenantsStore.currentTenant.id !== route.params.tenantId) {
    tenantsStore.fetchTenant(route.params.tenantId)
  }
})

// When switching between tenants, fetch the new tenant's data
watch(() => route.params.tenantId, (newId) => {
  if (newId) {
    tenantsStore.fetchTenant(newId)
  }
})
</script>

<style scoped>
.sidebar-link {
  @apply block w-full text-left py-2 px-4 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white transition-colors;
}
.router-link-exact-active {
  @apply bg-gray-800 text-orange-400 font-semibold;
}
</style>
