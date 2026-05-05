import axios from 'axios';
import { supabase } from '../supabase';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
});

// Auto-attach auth token to every request securely via the Supabase client.
// Calling getSession() here ensures that if the token is expired, Supabase 
// performs a background refresh and returns a fresh JWT before Axios proceeds.
apiClient.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// On 401, attempt a token refresh and retry the original request once.
// Only log the user out if the retried request also fails with a 401.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Ask Supabase to force-refresh the access token via the refresh token
      const { data, error: refreshError } = await supabase.auth.refreshSession();

      if (!refreshError && data.session?.access_token) {
        // Retry the original request with the fresh token
        originalRequest.headers['Authorization'] = `Bearer ${data.session.access_token}`;
        return apiClient(originalRequest);
      }

      // Refresh itself failed — the session is truly expired, log out
      const { useAuthStore } = await import('../stores/auth');
      const authStore = useAuthStore();
      if (authStore.user) {
        await authStore.handleSessionExpired();
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;