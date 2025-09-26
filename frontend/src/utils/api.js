import axios from 'axios';
import { useAuthStore } from '../stores/auth';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const authStore = useAuthStore();
    if (error.response && error.response.status === 401 && authStore.user) {
      await authStore.handleSessionExpired();
    }
    return Promise.reject(error);
  }
);

export default apiClient;