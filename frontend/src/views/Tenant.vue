<template>
  <div class="container mx-auto p-6">
    <div v-if="tenantsStore.currentTenant" class="mb-8 pb-4 border-b border-base-300">
      <h1 class="text-3xl font-bold flex items-center">
        <font-awesome-icon :icon="['fas', 'cogs']" class="mr-3 text-primary" />
        {{ tenantsStore.currentTenant.name }}
      </h1>
      <p class="text-base-content/70 mt-1">Manage your tenant settings, sources, and advanced configurations.</p>
    </div>
    <div v-else-if="tenantsStore.loading" class="text-center p-10">
      <p>Loading tenant...</p>
    </div>
    <div v-else class="text-center p-10 text-error">
      <p>Could not load tenant data. It might not exist or you may not have permission to view it.</p>
    </div>

    <div v-if="tenantsStore.currentTenant">
      <div class="mb-8">
        <nav class="flex space-x-4">
          <router-link :to="{ name: 'TenantSettings', params: { tenantId: tenantsStore.currentTenant.id } }" class="tenant-nav-link">
            <font-awesome-icon :icon="['fas', 'sliders']" class="mr-2" />
            Settings
          </router-link>
          <router-link :to="{ name: 'TenantSources', params: { tenantId: tenantsStore.currentTenant.id } }" class="tenant-nav-link">
            <font-awesome-icon :icon="['fas', 'database']" class="mr-2" />
            Sources
          </router-link>
          <router-link :to="{ name: 'TenantFineTune', params: { tenantId: tenantsStore.currentTenant.id } }" class="tenant-nav-link">
            <font-awesome-icon :icon="['fas', 'flask-vial']" class="mr-2" />
            Fine Tune
          </router-link>
        </nav>
      </div>

      <main>
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
  tenantsStore.fetchTenant(route.params.tenantId)
})

// When switching between tenants, fetch the new tenant's data
watch(() => route.params.tenantId, (newId) => {
  if (newId) {
    tenantsStore.fetchTenant(newId)
  }
})
</script>

<style scoped>
.tenant-nav-link {
  @apply py-2 px-4 rounded-lg text-base-content hover:bg-base-200 transition-colors;
}
.router-link-exact-active {
  @apply bg-primary/10 text-primary font-semibold;
}
</style>
