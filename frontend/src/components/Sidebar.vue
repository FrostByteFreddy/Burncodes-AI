<template>
  <div class="flex flex-col w-64 h-screen px-4 py-8 bg-brand-black border-r border-gray-700">
    <h2 class="text-3xl font-semibold text-center text-accent-gradient">SwiftAnswer</h2>

    <div class="relative mt-6">
      <div v-if="tenantsStore.tenants.length > 1">
        <button @click="dropdownOpen = !dropdownOpen" class="w-full px-4 py-2 text-left text-brand-white bg-gray-800 rounded-md hover:bg-gray-700 focus:outline-none focus:bg-gray-700">
          <span class="truncate">{{ activeTenant ? activeTenant.name : 'Select a Tenant' }}</span>
          <svg class="w-5 h-5 absolute right-2 top-2.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
        <div v-show="dropdownOpen" class="absolute right-0 w-full mt-2 py-2 bg-gray-800 rounded-md shadow-xl z-20">
          <a v-for="tenant in tenantsStore.tenants" :key="tenant.id" @click="selectTenant(tenant)" href="#" class="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-brand-white">
            {{ tenant.name }}
          </a>
        </div>
      </div>
      <div v-else-if="tenantsStore.tenants.length === 1" class="px-4 py-2 text-brand-white">
        <span class="font-semibold">{{ tenantsStore.tenants[0].name }}</span>
      </div>
    </div>

    <div class="flex flex-col justify-between flex-1 mt-6">
      <nav v-if="activeTenant">
        <router-link :to="{ name: 'TenantSources', params: { tenantId: activeTenant.id } }" class="flex items-center px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Sources</router-link>
        <router-link :to="{ name: 'TenantSettings', params: { tenantId: activeTenant.id } }" class="flex items-center px-4 py-2 mt-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Configuration</router-link>
        <router-link :to="{ name: 'TenantAdvanced', params: { tenantId: activeTenant.id } }" class="flex items-center px-4 py-2 mt-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Advanced</router-link>
        <a :href="`/chat/${activeTenant.id}`" target="_blank" class="flex items-center px-4 py-2 mt-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Chatbot</a>
      </nav>
      <div v-else class="text-center text-gray-500">
        <p>Select a tenant to see management options.</p>
      </div>

      <div>
        <h3 class="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Settings</h3>
        <router-link to="/profile" class="flex items-center px-4 py-2 mt-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Profile</router-link>
        <router-link to="/manage-tenants" class="flex items-center px-4 py-2 mt-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Manage Tenants</router-link>
        <router-link to="/subscription" class="flex items-center px-4 py-2 mt-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Subscription</router-link>
        <button @click="handleLogout" class="w-full flex items-center px-4 py-2 mt-2 text-gray-300 hover:bg-gray-700 hover:text-brand-white rounded-md">Logout</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const tenantsStore = useTenantsStore()
const authStore = useAuthStore()
const router = useRouter()

const dropdownOpen = ref(false)
const activeTenant = ref(null)

onMounted(async () => {
  await tenantsStore.fetchTenants()
  if (tenantsStore.tenants.length === 1) {
    selectTenant(tenantsStore.tenants[0])
  }
})

watch(() => tenantsStore.tenants, (newTenants) => {
  if (newTenants.length === 1 && !activeTenant.value) {
    selectTenant(newTenants[0]);
  }
  // If the active tenant is deleted, reset it
  if (activeTenant.value && !newTenants.find(t => t.id === activeTenant.value.id)) {
    activeTenant.value = null;
    router.push('/manage-tenants');
  }
}, { deep: true });


const selectTenant = (tenant) => {
  activeTenant.value = tenant
  dropdownOpen.value = false
  // Navigate to the tenant's settings page when a tenant is selected
  router.push({ name: 'TenantSettings', params: { tenantId: tenant.id } })
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
