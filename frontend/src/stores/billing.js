import { defineStore } from "pinia";
import { ref } from "vue";
import apiClient from "../utils/api";
import { useAuthStore } from "./auth";

export const useBillingStore = defineStore("billing", () => {
  const balance = ref(0.0);
  const usage = ref({ total_cost: 0.0, input_tokens: 0, output_tokens: 0 });
  const history = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const authStore = useAuthStore();

  const getAuthHeaders = () => {
    if (!authStore.session?.access_token) {
      throw new Error("User is not authenticated.");
    }
    return { Authorization: `Bearer ${authStore.session.access_token}` };
  };

  async function fetchBalance() {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.get("/billing/balance", {
        headers: getAuthHeaders(),
      });
      balance.value = response.data.balance_chf;
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to fetch balance";
    } finally {
      loading.value = false;
    }
  }

  async function fetchUsage() {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.get("/billing/usage", {
        headers: getAuthHeaders(),
      });
      usage.value = response.data;
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to fetch usage";
    } finally {
      loading.value = false;
    }
  }

  async function fetchHistory() {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.get("/billing/history", {
        headers: getAuthHeaders(),
      });
      history.value = response.data.history;
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to fetch history";
    } finally {
      loading.value = false;
    }
  }

  async function createCheckoutSession(amount = 20, isRecurring = false) {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.post(
        "/billing/create-checkout-session",
        { amount, is_recurring: isRecurring },
        { headers: getAuthHeaders() }
      );
      return response.data.url;
    } catch (e) {
      error.value =
        e.response?.data?.error || "Failed to create checkout session";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function getPortalUrl() {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.post(
        "/billing/portal",
        {},
        { headers: getAuthHeaders() }
      );
      return response.data.url;
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to get portal URL";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function verifySession(sessionId) {
    loading.value = true;
    error.value = null;
    try {
      await apiClient.post(
        "/billing/verify-session",
        { session_id: sessionId },
        { headers: getAuthHeaders() }
      );
      // Refresh balance after verification
      await fetchBalance();
    } catch (e) {
      error.value = e.response?.data?.error || "Failed to verify session";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  return {
    balance,
    usage,
    history,
    loading,
    error,
    fetchBalance,
    fetchUsage,
    fetchHistory,
    createCheckoutSession,
    getPortalUrl,
    verifySession,
  };
});
