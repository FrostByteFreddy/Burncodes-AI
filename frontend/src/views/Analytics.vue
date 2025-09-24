<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Chat Analytics</h1>
    <div class="bg-base-100 p-6 rounded-lg shadow-lg">
      <div class="flex justify-end mb-4">
        <select v-model="selectedTimeframe" @change="updateChart" class="select select-bordered">
          <option v-for="frame in timeframes" :key="frame.value" :value="frame.value">
            {{ frame.label }}
          </option>
        </select>
      </div>
      <div v-if="isLoading" class="flex justify-center items-center h-64">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
      <div v-else-if="error" class="text-error">
        {{ error }}
      </div>
      <div v-else>
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
import { useAuthStore } from '@/stores/auth';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const route = useRoute();
const authStore = useAuthStore();
const tenantId = ref(route.params.tenantId);
const chatLogs = ref([]);
const isLoading = ref(true);
const error = ref(null);

const timeframes = [
  { label: 'Last Hour', value: 1 },
  { label: 'Last 4 Hours', value: 4 },
  { label: 'Last 12 Hours', value: 12 },
  { label: 'Last 24 Hours', value: 24 },
  { label: 'Last 7 Days', value: 168 }
];
const selectedTimeframe = ref(24); // Default to 24 hours

const fetchData = async () => {
  try {
    isLoading.value = true;
    const token = authStore.session.access_token;
    const response = await axios.get(`${API_BASE_URL}/chat/${tenantId.value}/analytics`, {
      headers: {
        Authorization: `Bearer ${token}`
      },
      params: {
        timeframe: selectedTimeframe.value
      }
    });
    chatLogs.value = response.data;
  } catch (err) {
    error.value = 'Failed to load chat analytics. Please try again later.';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

const chartData = computed(() => {
  const data = {
    labels: [],
    datasets: [{
      label: 'Number of Chats',
      backgroundColor: '#f87979',
      data: []
    }]
  };

  if (chatLogs.value.length === 0) return data;

  chatLogs.value.forEach(log => {
    const date = new Date(log.time_bucket);
    const label = selectedTimeframe.value > 24 ? date.toLocaleDateString() : date.toLocaleTimeString();
    data.labels.push(label);
    data.datasets[0].data.push(log.chat_count);
  });

  return data;
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false
};

const updateChart = () => {
  // This is handled by computed properties, but we can keep this function for clarity
};

onMounted(() => {
  fetchData();
});
</script>