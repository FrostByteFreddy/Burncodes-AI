import { defineStore } from "pinia";
import { ref, watch } from "vue";
import apiClient from "../utils/api";
import { useAuthStore } from "./auth";

export const useTenantsStore = defineStore("tenants", () => {
  const tenants = ref([]);
  const currentTenant = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const authStore = useAuthStore();

  const getAuthHeaders = () => {
    if (!authStore.session?.access_token) {
      throw new Error("User is not authenticated.");
    }
    return { Authorization: `Bearer ${authStore.session.access_token}` };
  };

  async function restoreTenant() {
    const tenantId = localStorage.getItem("currentTenantId");
    if (tenantId) {
      await fetchTenant(tenantId);
    }
  }
  restoreTenant();

  async function fetchTenants() {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.get(`/tenants`, {
        headers: getAuthHeaders(),
      });
      tenants.value = response.data;
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to fetch tenants";
    } finally {
      loading.value = false;
    }
  }

  async function fetchTenant(id) {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.get(`/tenants/${id}`, {
        headers: getAuthHeaders(),
      });
      currentTenant.value = response.data;
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to fetch tenant";
      currentTenant.value = null;
    } finally {
      loading.value = false;
    }
  }

  async function createTenant(tenantData) {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.post(`/tenants`, tenantData, {
        headers: getAuthHeaders(),
      });
      tenants.value.push(response.data);
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to create tenant";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function updateTenant(id, tenantData) {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.put(
        `/tenants/${id}`,
        tenantData,
        { headers: getAuthHeaders() }
      );
      const index = tenants.value.findIndex((t) => t.id === id);
      if (index !== -1) {
        tenants.value[index] = response.data;
      }
      currentTenant.value = response.data;
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to update tenant";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function deleteTenant(id) {
    loading.value = true;
    error.value = null;
    try {
      await apiClient.delete(`/tenants/${id}`, {
        headers: getAuthHeaders(),
      });
      tenants.value = tenants.value.filter((t) => t.id !== id);
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to delete tenant";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function selectTenant(tenant) {
    currentTenant.value = tenant;
  }

  watch(currentTenant, (newTenant) => {
    if (newTenant) {
      localStorage.setItem("currentTenantId", newTenant.id);
    } else {
      localStorage.removeItem("currentTenantId");
    }
  });

  return {
    tenants,
    currentTenant,
    loading,
    error,
    fetchTenants,
    fetchTenant,
    createTenant,
    updateTenant,
    deleteTenant,
    selectTenant,
  };
});
