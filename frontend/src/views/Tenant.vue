<template>
  <div class="container mx-auto p-6" v-if="tenantsStore.currentTenant">
    <div class="mb-6">
      <h1 class="text-3xl font-bold">{{ tenantsStore.currentTenant.name }}</h1>
      <p class="text-gray-400">Manage your tenant settings, sources, and advanced configurations.</p>
    </div>

    <div class="flex border-b border-gray-700 mb-6">
      <router-link :to="{ name: 'TenantSettings' }" class="tab-link">Settings</router-link>
      <router-link :to="{ name: 'TenantSources' }" class="tab-link">Sources</router-link>
      <router-link :to="{ name: 'TenantAdvanced' }" class="tab-link">Advanced</router-link>
    </div>

    <div>
      <router-view />
    </div>
  </div>
  <div v-else-if="tenantsStore.loading" class="text-center p-10">
    <p>Loading tenant...</p>
  </div>
  <div v-else class="text-center p-10 text-red-400">
    <p>Could not load tenant data. It might not exist or you may not have permission to view it.</p>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useRoute } from 'vue-router'

const tenantsStore = useTenantsStore()
const route = useRoute()

onMounted(() => {
  tenantsStore.fetchTenant(route.params.tenantId)
})

watch(() => route.params.tenantId, (newId) => {
  if (newId) {
    tenantsStore.fetchTenant(newId)
  }
})
</script>

<style scoped>
.tab-link {
  @apply py-2 px-4 text-gray-400 hover:text-white;
}
.router-link-exact-active {
  @apply text-orange-400 border-b-2 border-orange-400;
}
</style>
