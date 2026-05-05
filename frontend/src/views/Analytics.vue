<template>
  <div>
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 border-b border-base-200/50 pb-6 gap-4">
      <h3 class="text-2xl font-bold text-base-content flex items-center">
        <font-awesome-icon
          :icon="['fas', 'chart-line']"
          class="mr-3 text-primary"
        />
        {{ $t("analytics.title") }}
      </h3>
      <div class="flex flex-wrap items-center gap-3">
        <select
          v-model="selectedInterval"
          @change="updateChart"
          class="select select-bordered rounded-xl bg-base-100 font-medium focus:ring-2 focus:ring-primary/50 transition-shadow border-base-200"
        >
          <option v-for="item in intervals" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
        </select>
        <select
          v-model="selectedTimeframe"
          @change="updateChart"
          class="select select-bordered rounded-xl bg-base-100 font-medium focus:ring-2 focus:ring-primary/50 transition-shadow border-base-200"
        >
          <option
            v-for="frame in timeframes"
            :key="frame.value"
            :value="frame.value"
          >
            {{ frame.label }}
          </option>
        </select>
      </div>
    </div>
    
    <div v-if="isLoading" class="flex justify-center items-center h-80 bg-base-100 rounded-xl border border-base-200/50 shadow-sm animate-pulse">
      <span class="loading loading-spinner text-primary loading-lg"></span>
    </div>
    
    <div v-else-if="error" class="flex justify-center items-center h-80 bg-error/10 text-error rounded-xl border border-error/20 p-6">
      <div class="text-center">
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="text-4xl mb-3" />
        <p class="font-bold text-lg">{{ $t("analytics.error") }}</p>
      </div>
    </div>
    
    <div v-else class="bg-base-100 p-6 rounded-xl shadow-sm border border-base-200/50">
      <div class="chart-container">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import apiClient from "@/utils/api";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler,
} from "chart.js";
import { useAuthStore } from "@/stores/auth";
import { useI18n } from "vue-i18n";

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler
);

const { t } = useI18n();



const route = useRoute();
const authStore = useAuthStore();
const tenantId = ref(route.params.tenantId);
const chatLogs = ref([]);
const isLoading = ref(true);
const error = ref(null);

const timeframes = computed(() => [
  { label: t("analytics.timeframes.lastHour"), value: 1 },
  { label: t("analytics.timeframes.last4Hours"), value: 4 },
  { label: t("analytics.timeframes.last12Hours"), value: 12 },
  { label: t("analytics.timeframes.last24Hours"), value: 24 },
  { label: t("analytics.timeframes.last7Days"), value: 168 },
]);
const selectedTimeframe = ref(24);

const intervals = computed(() => [
  { label: t("analytics.intervals.perMinute"), value: "minute" },
  { label: t("analytics.intervals.per5Minutes"), value: "5-minute" }, // 1. Added new interval option
  { label: t("analytics.intervals.perHour"), value: "hour" },
  { label: t("analytics.intervals.perDay"), value: "day" },
]);
const selectedInterval = ref("hour");

const fetchData = async () => {
  try {
    isLoading.value = true;
    const token = authStore.session.access_token;
    const response = await apiClient.get(
      `/chat/${tenantId.value}/analytics`,
      {
        params: {
          timeframe: selectedTimeframe.value,
          interval: selectedInterval.value,
        },
      }
    );
    chatLogs.value = response.data;
  } catch (err) {
    error.value = t("analytics.error");
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

const chartData = computed(() => {
  const data = {
    labels: [],
    datasets: [
      {
        label: t("analytics.chartLabel"),
        backgroundColor: "rgba(10, 31, 171, 0.15)", // Indigo with opacity
        borderColor: "rgba(10, 31, 171, 1)", // Indigo
        borderWidth: 3,
        pointBackgroundColor: "rgba(10, 31, 171, 1)",
        pointBorderColor: "#fff",
        pointHoverBackgroundColor: "#fff",
        pointHoverBorderColor: "rgba(10, 31, 171, 1)",
        fill: true,
        tension: 0.4,
        data: [],
      },
    ],
  };

  if (chatLogs.value.length === 0) return data;

  const allBuckets = new Map();
  const now = new Date();
  const timeframeHours = selectedTimeframe.value;
  const interval = selectedInterval.value;

  let timeUnit, timeFormat;
  // 2. Added logic to define the time unit for 5 minutes
  if (interval === "minute") {
    timeUnit = 60 * 1000;
    timeFormat = { hour: "2-digit", minute: "2-digit" };
  } else if (interval === "5-minute") {
    timeUnit = 5 * 60 * 1000;
    timeFormat = { hour: "2-digit", minute: "2-digit" };
  } else if (interval === "day") {
    timeUnit = 24 * 60 * 60 * 1000;
    timeFormat = { year: "numeric", month: "2-digit", day: "2-digit" };
  } else {
    // hour
    timeUnit = 60 * 60 * 1000;
    timeFormat = { hour: "2-digit", minute: "2-digit" };
  }

  const totalUnits = Math.ceil((timeframeHours * (60 * 60 * 1000)) / timeUnit);

  for (let i = 0; i < totalUnits; i++) {
    const date = new Date(now.getTime() - i * timeUnit);
    let bucket;
    // 3. Added logic to create 5-minute buckets
    if (interval === "minute") {
      bucket = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
        date.getHours(),
        date.getMinutes()
      ).toISOString();
    } else if (interval === "5-minute") {
      const roundedMinutes = date.getMinutes() - (date.getMinutes() % 5);
      bucket = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
        date.getHours(),
        roundedMinutes
      ).toISOString();
    } else if (interval === "day") {
      bucket = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate()
      ).toISOString();
    } else {
      // hour
      bucket = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
        date.getHours()
      ).toISOString();
    }
    allBuckets.set(bucket.slice(0, -5) + "Z", 0);
  }

  chatLogs.value.forEach((log) => {
    const bucket = new Date(log.time_bucket).toISOString();
    if (allBuckets.has(bucket.slice(0, -5) + "Z")) {
      allBuckets.set(bucket.slice(0, -5) + "Z", log.message_count);
    }
  });

  const sortedBuckets = Array.from(allBuckets.keys()).sort();

  sortedBuckets.forEach((bucket) => {
    const date = new Date(bucket);
    const label = date.toLocaleString("default", timeFormat);
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
      beginAtZero: true,
    },
  },
  plugins: {
    legend: {
      display: false,
    },
  },
};

const updateChart = () => {
  fetchData();
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.chart-container {
  height: 400px;
  min-width: 100%;
}
</style>
