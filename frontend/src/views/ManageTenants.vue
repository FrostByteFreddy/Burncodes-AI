<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-4xl font-bold text-base-content">
        {{ $t("manageTenants.title") }}
      </h1>
      <div v-if="tenantsStore.tenants.length !== 0">
        <button @click="showCreateModal = true" class="btn btn-primary">
          <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
          {{ $t("manageTenants.newTenant") }}
        </button>
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div
      v-if="tenantsStore.loading && tenantsStore.tenants.length === 0"
      class="space-y-4"
    >
      <div
        v-for="n in 3"
        :key="n"
        class="h-24 bg-base-200 rounded-lg animate-pulse"
      ></div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!tenantsStore.loading && tenantsStore.tenants.length === 0"
      class="text-center bg-base-100 p-12 rounded-lg shadow-md"
    >
      <font-awesome-icon
        :icon="['fas', 'folder-open']"
        class="text-5xl text-base-content/20 mb-4"
      />
      <h2 class="text-2xl font-semibold mb-2">
        {{ $t("manageTenants.noTenants") }}
      </h2>
      <p class="text-base-content/70 mb-6">
        {{ $t("manageTenants.startMessage") }}
      </p>
      <div v-if="tenantsStore.tenants.length === 0">
        <button @click="showCreateModal = true" class="btn btn-primary">
          <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
          {{ $t("manageTenants.createTenant") }}
        </button>
      </div>
    </div>

    <!-- Tenant List -->
    <div v-else class="space-y-4">
      <div
        v-for="tenant in tenantsStore.tenants"
        :key="tenant.id"
        class="bg-base-100 p-6 rounded-lg flex justify-between items-center shadow-md"
      >
        <div>
          <h2 class="text-xl font-bold">{{ tenant.name }}</h2>
        </div>
        <div class="flex space-x-4">
          <button
            @click="confirmDelete(tenant)"
            class="btn btn-sm text-error hover:bg-error/10"
          >
            <font-awesome-icon :icon="['fas', 'trash']" class="mr-2" />
            {{ $t("manageTenants.delete") }}
          </button>
        </div>
      </div>
    </div>

    <CreateTenantModal
      :show="showCreateModal"
      @close="showCreateModal = false"
      @create="handleCreateTenant"
    />

    <ConfirmationModal
      :show="showConfirmationModal"
      :title="$t('manageTenants.deleteModal.title')"
      :message="
        $t('manageTenants.deleteModal.message', { name: tenantToDelete?.name })
      "
      :confirmationText="tenantToDelete?.name"
      :confirmButtonText="$t('manageTenants.deleteModal.confirm')"
      @confirm="handleDeleteTenant"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useTenantsStore } from "../stores/tenants";
import { useToast } from "../composables/useToast";
import CreateTenantModal from "../components/CreateTenantModal.vue";
import ConfirmationModal from "../components/ConfirmationModal.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const showCreateModal = ref(false);
const tenantToDelete = ref(null);
const showConfirmationModal = ref(false);

onMounted(() => {
  tenantsStore.fetchTenants();
});

const handleCreateTenant = async (tenantData) => {
  try {
    await tenantsStore.createTenant(tenantData);
    showCreateModal.value = false;
    addToast(t("manageTenants.toast.createSuccess"), "success");
  } catch (error) {
    addToast(t("manageTenants.toast.createError"), "error");
  }
};

const confirmDelete = (tenant) => {
  tenantToDelete.value = tenant;
  showConfirmationModal.value = true;
};

const cancelDelete = () => {
  tenantToDelete.value = null;
  showConfirmationModal.value = false;
};

const handleDeleteTenant = async () => {
  if (tenantToDelete.value) {
    try {
      await tenantsStore.deleteTenant(tenantToDelete.value.id);
      addToast(t("manageTenants.toast.deleteSuccess"), "success");
      tenantToDelete.value = null;
      showConfirmationModal.value = false;
    } catch (error) {
      addToast(t("manageTenants.toast.deleteError"), "error");
    }
  }
};
</script>
