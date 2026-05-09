<template>
  <div class="page">
    <div class="page-header">
      <p class="page-label">{{ $t('analytics.title').toUpperCase() }}</p>
      <div class="header-controls">
        <select v-model="selectedInterval" @change="fetchAnalytics" class="field__select">
          <option v-for="item in intervals" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
        <select v-model="selectedTimeframe" @change="fetchAnalytics" class="field__select">
          <option v-for="frame in timeframes" :key="frame.value" :value="frame.value">{{ frame.label }}</option>
        </select>
      </div>
    </div>

    <!-- Chart panel -->
    <div class="chart-card">
      <div v-if="analyticsLoading" class="chart-loading">
        <font-awesome-icon :icon="['fas', 'spinner']" class="spin" />
      </div>
      <div v-else-if="analyticsError" class="chart-error">
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
        <p>{{ $t('analytics.error') }}</p>
      </div>
      <div v-else class="chart-wrap">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>

    <!-- Chat logs section -->
    <div class="section-header" style="margin-top:32px; margin-bottom:20px;">
      <span class="section-label">{{ $t('chatLogs.title').toUpperCase() }}</span>
      <div class="section-line"></div>
    </div>

    <!-- Loading -->
    <div v-if="logsLoading" class="skeleton-block" style="height:200px;"></div>

    <!-- Error -->
    <div v-else-if="logsError" class="chart-error card">
      <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
      <p>{{ logsError }}</p>
    </div>

    <!-- Conversation detail -->
    <div v-else-if="selectedConversation" class="card log-detail">
      <button @click="selectedConversation = null" class="btn-back">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
        {{ $t('chatLogs.back') }}
      </button>
      <div ref="chatContainer" class="chat-scroll">
        <div v-for="log in conversationLogs" :key="log.id" class="chat-pair">
          <div v-if="log.user_message" class="bubble bubble--user">{{ log.user_message }}</div>
          <div v-if="log.ai_message" class="bubble bubble--bot" v-html="processBotMessage(log.ai_message).html"></div>
        </div>
      </div>
    </div>

    <!-- Conversation list -->
    <div v-else class="card log-list">
      <div v-if="!conversations.length" class="empty-logs">
        <font-awesome-icon :icon="['fas', 'comments']" />
        <p>{{ $t('chatLogs.conversations') }}</p>
      </div>
      <div
        v-for="convo in conversations"
        :key="convo.conversation_id"
        @click="selectConversation(convo.conversation_id)"
        class="log-row"
      >
        <div class="log-row__content">
          <p class="log-row__preview">{{ convo.first_message || $t('chatLogs.noMessage') }}</p>
          <div class="log-row__meta">
            <span class="meta-chip">
              <font-awesome-icon :icon="['fas', 'comments']" />
              {{ convo.message_count }}
            </span>
            <span class="meta-chip">
              <font-awesome-icon :icon="['fas', 'coins']" />
              CHF {{ (convo.total_cost || 0).toFixed(4) }}
            </span>
          </div>
        </div>
        <div class="log-row__right">
          <span class="log-row__time">{{ new Date(convo.last_active).toLocaleString() }}</span>
          <font-awesome-icon :icon="['fas', 'chevron-right']" class="log-row__arrow" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import apiClient from '@/utils/api'
import { useTenantsStore } from '@/stores/tenants'
import { useToast } from '@/composables/useToast'
import { processBotMessage } from '@/utils/chatProcessor.js'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, Title, Tooltip, Legend,
  LineElement, PointElement, CategoryScale, LinearScale, Filler,
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale, Filler)

const { t } = useI18n()
const route = useRoute()
const tenantsStore = useTenantsStore()
const { addToast } = useToast()

// ── Analytics ────────────────────────────────────────────────────────────────
const analyticsData = ref([])
const analyticsLoading = ref(true)
const analyticsError = ref(null)

const timeframes = computed(() => [
  { label: t('analytics.timeframes.lastHour'), value: 1 },
  { label: t('analytics.timeframes.last4Hours'), value: 4 },
  { label: t('analytics.timeframes.last12Hours'), value: 12 },
  { label: t('analytics.timeframes.last24Hours'), value: 24 },
  { label: t('analytics.timeframes.last7Days'), value: 168 },
])
const selectedTimeframe = ref(24)

const intervals = computed(() => [
  { label: t('analytics.intervals.perMinute'), value: 'minute' },
  { label: t('analytics.intervals.per5Minutes'), value: '5-minute' },
  { label: t('analytics.intervals.perHour'), value: 'hour' },
  { label: t('analytics.intervals.perDay'), value: 'day' },
])
const selectedInterval = ref('hour')

const fetchAnalytics = async () => {
  const tenantId = tenantsStore.currentTenant?.id || route.params.tenantId
  if (!tenantId) return
  try {
    analyticsLoading.value = true
    const response = await apiClient.get(`/chat/${tenantId}/analytics`, {
      params: { timeframe: selectedTimeframe.value, interval: selectedInterval.value },
    })
    analyticsData.value = response.data
  } catch {
    analyticsError.value = t('analytics.error')
  } finally {
    analyticsLoading.value = false
  }
}

const chartData = computed(() => {
  const data = {
    labels: [],
    datasets: [{
      label: t('analytics.chartLabel'),
      backgroundColor: 'rgba(10, 31, 171, 0.10)',
      borderColor: 'rgba(10, 31, 171, 0.9)',
      borderWidth: 2,
      pointBackgroundColor: 'rgba(10, 31, 171, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(10, 31, 171, 1)',
      fill: true,
      tension: 0.4,
      data: [],
    }],
  }
  if (!analyticsData.value.length) return data
  const allBuckets = new Map()
  const now = new Date()
  const interval = selectedInterval.value
  let timeUnit, timeFormat
  if (interval === 'minute') { timeUnit = 60000; timeFormat = { hour: '2-digit', minute: '2-digit' } }
  else if (interval === '5-minute') { timeUnit = 300000; timeFormat = { hour: '2-digit', minute: '2-digit' } }
  else if (interval === 'day') { timeUnit = 86400000; timeFormat = { year: 'numeric', month: '2-digit', day: '2-digit' } }
  else { timeUnit = 3600000; timeFormat = { hour: '2-digit', minute: '2-digit' } }

  const totalUnits = Math.ceil((selectedTimeframe.value * 3600000) / timeUnit)
  for (let i = 0; i < totalUnits; i++) {
    const date = new Date(now.getTime() - i * timeUnit)
    let bucket
    if (interval === 'minute') bucket = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes()).toISOString()
    else if (interval === '5-minute') { const rm = date.getMinutes() - (date.getMinutes() % 5); bucket = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), rm).toISOString() }
    else if (interval === 'day') bucket = new Date(date.getFullYear(), date.getMonth(), date.getDate()).toISOString()
    else bucket = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours()).toISOString()
    allBuckets.set(bucket.slice(0, -5) + 'Z', 0)
  }
  analyticsData.value.forEach((log) => {
    const bucket = new Date(log.time_bucket).toISOString()
    if (allBuckets.has(bucket.slice(0, -5) + 'Z')) allBuckets.set(bucket.slice(0, -5) + 'Z', log.message_count)
  })
  Array.from(allBuckets.keys()).sort().forEach((bucket) => {
    data.labels.push(new Date(bucket).toLocaleString('default', timeFormat))
    data.datasets[0].data.push(allBuckets.get(bucket))
  })
  return data
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: 'rgba(160,168,200,0.8)' },
    },
    x: {
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: 'rgba(160,168,200,0.8)', maxTicksLimit: 12 },
    },
  },
  plugins: { legend: { display: false } },
}

// ── Chat Logs ────────────────────────────────────────────────────────────────
const conversations = ref([])
const conversationLogs = ref([])
const selectedConversation = ref(null)
const logsLoading = ref(false)
const logsError = ref(null)
const chatContainer = ref(null)

const fetchConversations = async () => {
  if (!tenantsStore.currentTenant) return
  try {
    logsLoading.value = true
    logsError.value = null
    const response = await apiClient.get(`/chat/${tenantsStore.currentTenant.id}/conversations`)
    conversations.value = response.data
  } catch {
    logsError.value = t('chatLogs.errors.loadConversations')
  } finally {
    logsLoading.value = false
  }
}

const selectConversation = async (conversationId) => {
  try {
    logsLoading.value = true
    selectedConversation.value = conversationId
    const response = await apiClient.get(`/chat/${tenantsStore.currentTenant.id}/conversation/${conversationId}`)
    conversationLogs.value = response.data
    await nextTick()
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  } catch {
    addToast(t('chatLogs.errors.loadLogs'), 'error')
    selectedConversation.value = null
  } finally {
    logsLoading.value = false
  }
}

watch(() => tenantsStore.currentTenant, (tenant) => {
  if (tenant) {
    fetchAnalytics()
    fetchConversations()
    selectedConversation.value = null
    conversations.value = []
  }
}, { immediate: true })
</script>

<style scoped>
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 24px;
}
.page-label {
  font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em; color: var(--surface-muted);
}
.header-controls { display: flex; gap: 8px; }
.field__select {
  padding: 7px 12px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-text);
  font-size: 12px; font-weight: 500;
  cursor: pointer; outline: none;
  transition: border-color var(--t-fast);
}
.field__select:focus { border-color: var(--brand-indigo); }

/* Chart */
.chart-card {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  padding: 24px;
  min-height: 340px;
  display: flex; align-items: center; justify-content: center;
}
.chart-wrap { width: 100%; height: 300px; }
.chart-loading { font-size: 28px; color: var(--brand-indigo); }
.chart-error {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  color: var(--status-error); font-size: 22px;
}
.chart-error p { font-size: 13px; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Section header */
.section-header { display: flex; align-items: center; gap: 12px; }
.section-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; color: var(--surface-muted); white-space: nowrap; }
.section-line { flex: 1; height: 1px; background: var(--surface-3); }

/* Skeleton */
.skeleton-block {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

/* Card */
.card {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* Back button */
.btn-back {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  background: none; border: none;
  color: var(--surface-muted);
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: color var(--t-fast);
}
.btn-back:hover { color: var(--surface-text); }

/* Chat scroll */
.chat-scroll { max-height: 60vh; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 16px; scroll-behavior: smooth; }
.chat-pair { display: flex; flex-direction: column; gap: 8px; }
.bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  font-size: 14px; line-height: 1.6;
}
.bubble--user {
  align-self: flex-end;
  background: var(--gradient-brand);
  color: white;
  border-bottom-right-radius: 4px;
}
.bubble--bot {
  align-self: flex-start;
  background: var(--surface-2);
  color: var(--surface-text);
  border-bottom-left-radius: 4px;
}

/* Log list */
.log-list { }
.empty-logs {
  padding: 40px; text-align: center;
  color: var(--surface-muted);
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  font-size: 28px;
}
.empty-logs p { font-size: 13px; }
.log-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--surface-3);
  cursor: pointer;
  transition: background var(--t-fast);
}
.log-row:last-child { border-bottom: none; }
.log-row:hover { background: var(--surface-2); }
.log-row__content { flex: 1; min-width: 0; }
.log-row__preview {
  font-size: 14px; font-weight: 600; color: var(--surface-heading);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 6px;
}
.log-row__meta { display: flex; gap: 8px; }
.meta-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-pill);
  font-size: 11px; font-weight: 500; color: var(--surface-muted);
}
.log-row__right { display: flex; align-items: center; gap: 10px; margin-left: 16px; flex-shrink: 0; }
.log-row__time { font-size: 11px; color: var(--surface-muted); }
.log-row__arrow { font-size: 12px; color: var(--surface-muted); transition: color var(--t-fast); }
.log-row:hover .log-row__arrow { color: var(--brand-indigo); }
</style>
