<template>
  <div class="p-8">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-4xl font-bold text-brand-white">Manage Tenants</h1>
      <button @click="showCreateModal = true" class="bg-black border border-white hover:bg-gray-900 text-white font-bold py-2 px-6 rounded-lg">
        New Tenant
      </button>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="tenantsStore.loading && tenantsStore.tenants.length === 0" class="space-y-4">
      <div v-for="n in 3" :key="n" class="h-24 bg-gray-800 rounded-lg animate-pulse"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!tenantsStore.loading && tenantsStore.tenants.length === 0" class="text-center bg-gray-800 p-12 rounded-lg">
      <h2 class="text-2xl font-semibold mb-2">No tenants yet</h2>
      <p class="text-gray-400 mb-6">Create your first tenant to get started.</p>
      <button @click="showCreateModal = true" class="bg-black border border-white hover:bg-gray-900 text-white font-bold py-2 px-6 rounded-lg">
        Create a Tenant
      </button>
    </div>

    <!-- Tenant List -->
    <div v-else class="space-y-4">
      <div v-for="tenant in tenantsStore.tenants" :key="tenant.id" class="bg-gray-800 p-6 rounded-lg flex justify-between items-center">
        <div>
          <h2 class="text-xl font-bold">{{ tenant.name }}</h2>
        </div>
        <div class="flex space-x-4">
          <button @click="confirmDelete(tenant)" class="text-red-500 hover:text-red-400 font-semibold">Delete</button>
        </div>
      </div>
    </div>

    <CreateTenantModal :show="showCreateModal" @close="showCreateModal = false" @create="handleCreateTenant" />

    <ConfirmationModal
      :show="showConfirmationModal"
      title="Delete Tenant"
      :message="`Are you sure you want to delete the tenant '${tenantToDelete?.name}'? This action cannot be undone.`"
      :confirmationText="tenantToDelete?.name"
      confirmButtonText="Delete"
      @confirm="handleDeleteTenant"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useToast } from '../composables/useToast'
import CreateTenantModal from '../components/CreateTenantModal.vue'
import ConfirmationModal from '../components/ConfirmationModal.vue'

const tenantsStore = useTenantsStore()
const { addToast } = useToast()
const showCreateModal = ref(false)
const tenantToDelete = ref(null)
const showConfirmationModal = ref(false)

onMounted(() => {
  tenantsStore.fetchTenants()
})

const handleCreateTenant = async (tenantData) => {
  try {
    await tenantsStore.createTenant(tenantData);
    showCreateModal.value = false;
    addToast('Tenant created successfully!', 'success');
  } catch (error) {
    addToast('Failed to create tenant.', 'error');
  }
}

const confirmDelete = (tenant) => {
  tenantToDelete.value = tenant;
  showConfirmationModal.value = true;
}

const cancelDelete = () => {
  tenantToDelete.value = null;
  showConfirmationModal.value = false;
}

const handleDeleteTenant = async () => {
  if (tenantToDelete.value) {
    try {
      await tenantsStore.deleteTenant(tenantToDelete.value.id);
      addToast('Tenant deleted successfully!', 'success');
      tenantToDelete.value = null;
      showConfirmationModal.value = false;
    } catch (error) {
      addToast('Failed to delete tenant.', 'error');
    }
  }
}
</script>
