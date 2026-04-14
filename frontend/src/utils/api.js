import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
});

// Auto-attach auth token to every request
apiClient.interceptors.request.use(async (config) => {
  const { useAuthStore } = await import('../stores/auth');
  const authStore = useAuthStore();
  if (authStore.session?.access_token) {
    config.headers.Authorization = `Bearer ${authStore.session.access_token}`;
  }
  return config;
});

// Auto-logout on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { useAuthStore } = await import('../stores/auth');
    const authStore = useAuthStore();
    if (error.response && error.response.status === 401 && authStore.user) {
      await authStore.handleSessionExpired();
    }
    return Promise.reject(error);
  }
);

export default apiClient;