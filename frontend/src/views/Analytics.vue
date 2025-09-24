<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Chat Analytics</h1>
    <div class="bg-base-100 p-6 rounded-lg shadow-lg">
      <div class="flex justify-end gap-4 mb-4">
        <select v-model="selectedInterval" @change="updateChart" class="select select-bordered">
          <option v-for="item in intervals" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
        </select>
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
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { Line } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale, Filler } from 'chart.js';
import { useAuthStore } from '@/stores/auth';

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale, Filler);

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
const selectedTimeframe = ref(24);

const intervals = [
  { label: 'Per Minute', value: 'minute' },
  { label: 'Per Hour', value: 'hour' },
  { label: 'Per Day', value: 'day' }
];
const selectedInterval = ref('hour');

const fetchData = async () => {
  try {
    isLoading.value = true;
    const token = authStore.session.access_token;
    const response = await axios.get(`${API_BASE_URL}/chat/${tenantId.value}/analytics`, {
      headers: {
        Authorization: `Bearer ${token}`
      },
      params: {
        timeframe: selectedTimeframe.value,
        interval: selectedInterval.value
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
      label: 'Number of Messages',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 2,
      pointBackgroundColor: 'rgba(75, 192, 192, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(75, 192, 192, 1)',
      fill: true,
      tension: 0.4,
      data: []
    }]
  };

  if (chatLogs.value.length === 0) return data;

  const allBuckets = new Map();
  const now = new Date();
  const timeframeHours = selectedTimeframe.value;
  const interval = selectedInterval.value;

  let timeUnit, timeFormat;
  if (interval === 'minute') {
    timeUnit = 60 * 1000;
    timeFormat = { hour: '2-digit', minute: '2-digit' };
  } else if (interval === 'day') {
    timeUnit = 24 * 60 * 60 * 1000;
    timeFormat = { year: 'numeric', month: '2-digit', day: '2-digit' };
  } else { // hour
    timeUnit = 60 * 60 * 1000;
    timeFormat = { hour: '2-digit', minute: '2-digit' };
  }

  const totalUnits = timeframeHours * (60 * 60 * 1000) / timeUnit;

  for (let i = 0; i < totalUnits; i++) {
    const date = new Date(now.getTime() - i * timeUnit);
    let bucket;
    if (interval === 'minute') {
      bucket = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes()).toISOString();
    } else if (interval === 'day') {
      bucket = new Date(date.getFullYear(), date.getMonth(), date.getDate()).toISOString();
    } else { // hour
      bucket = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours()).toISOString();
    }
    allBuckets.set(bucket.slice(0, -5) + "Z", 0);
  }

  chatLogs.value.forEach(log => {
    const bucket = new Date(log.time_bucket).toISOString();
    if (allBuckets.has(bucket.slice(0,-5) + "Z")) {
      allBuckets.set(bucket.slice(0,-5) + "Z", log.message_count);
    }
  });

  const sortedBuckets = Array.from(allBuckets.keys()).sort();

  sortedBuckets.forEach(bucket => {
    const date = new Date(bucket);
    const label = date.toLocaleString([], timeFormat);
    data.labels.push(label);
    data.datasets[0].data.push(allBuckets.get(bucket));
  });

  return data;
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true
    }
  },
  plugins: {
    legend: {
      display: false
    }
  }
};

const updateChart = () => {
  fetchData();
};

onMounted(() => {
  fetchData();
});
</script>