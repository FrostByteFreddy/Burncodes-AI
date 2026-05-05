<template>
  <div>
    <!-- Internal tab switcher -->
    <div class="inline-flex p-1 space-x-1 bg-base-200 rounded-full mb-6">
      <a
        class="btn border-0 rounded-full hover:cursor-pointer space-x-2"
        :class="activeTab === 'analytics' ? '!bg-primary-focus text-primary-content shadow' : 'btn-ghost text-base-content'"
        @click="activeTab = 'analytics'"
      >
        <font-awesome-icon :icon="['fas', 'chart-line']" />
        <span>{{ $t('analytics.title') }}</span>
      </a>
      <a
        class="btn border-0 rounded-full hover:cursor-pointer space-x-2"
        :class="activeTab === 'chatlogs' ? '!bg-primary-focus text-primary-content shadow' : 'btn-ghost text-base-content'"
        @click="activeTab = 'chatlogs'; fetchConversations()"
      >
        <font-awesome-icon :icon="['fas', 'comments']" />
        <span>{{ $t('chatLogs.title') }}</span>
      </a>
    </div>

    <!-- ── Analytics ──────────────────────────────────────────── -->
    <div v-show="activeTab === 'analytics'">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 border-b border-base-200/50 pb-6 gap-4">
        <h3 class="text-2xl font-bold text-base-content flex items-center">
          <font-awesome-icon :icon="['fas', 'chart-line']" class="mr-3 text-primary" />
          {{ $t('analytics.title') }}
        </h3>
        <div class="flex flex-wrap items-center gap-3">
          <select v-model="selectedInterval" @change="fetchAnalytics" class="select select-bordered rounded-xl bg-base-100 font-medium focus:ring-2 focus:ring-primary/50 border-base-200">
            <option v-for="item in intervals" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
          <select v-model="selectedTimeframe" @change="fetchAnalytics" class="select select-bordered rounded-xl bg-base-100 font-medium focus:ring-2 focus:ring-primary/50 border-base-200">
            <option v-for="frame in timeframes" :key="frame.value" :value="frame.value">{{ frame.label }}</option>
          </select>
        </div>
      </div>

      <div v-if="analyticsLoading" class="flex justify-center items-center h-80 bg-base-100 rounded-xl border border-base-200/50 shadow-sm animate-pulse">
        <span class="loading loading-spinner text-primary loading-lg"></span>
      </div>
      <div v-else-if="analyticsError" class="flex justify-center items-center h-80 bg-error/10 text-error rounded-xl border border-error/20 p-6">
        <div class="text-center">
          <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="text-4xl mb-3" />
          <p class="font-bold text-lg">{{ $t('analytics.error') }}</p>
        </div>
      </div>
      <div v-else class="bg-base-100 p-6 rounded-xl shadow-sm border border-base-200/50">
        <div class="chart-container">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>

    <!-- ── Chat Logs ──────────────────────────────────────────── -->
    <div v-show="activeTab === 'chatlogs'">
      <div class="flex justify-between items-center mb-8 border-b border-base-200/50 pb-6">
        <h3 class="text-2xl font-bold text-base-content flex items-center">
          <font-awesome-icon :icon="['fas', 'comments']" class="mr-3 text-primary" />
          {{ $t('chatLogs.title') }}
        </h3>
      </div>

      <div v-if="logsLoading" class="flex justify-center items-center h-80 bg-base-100 rounded-xl border border-base-200/50 shadow-sm animate-pulse">
        <span class="loading loading-spinner text-primary loading-lg"></span>
      </div>
      <div v-else-if="logsError" class="flex justify-center items-center h-80 bg-error/10 text-error rounded-xl border border-error/20 p-6">
        <div class="text-center">
          <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="text-4xl mb-3" />
          <p class="font-bold text-lg">{{ logsError }}</p>
        </div>
      </div>
      <div v-else>
        <!-- Conversation detail -->
        <div v-if="selectedConversation" class="bg-base-100 rounded-xl p-6 shadow-sm border border-base-200/50">
          <button @click="selectedConversation = null" class="btn btn-ghost mb-6">
            <font-awesome-icon :icon="['fas', 'arrow-left']" />
            {{ $t('chatLogs.back') }}
          </button>
          <div ref="chatContainer" class="max-h-[60vh] overflow-y-auto space-y-6 px-2 scroll-smooth">
            <div v-for="log in conversationLogs" :key="log.id">
              <div v-if="log.user_message" class="chat chat-end">
                <div class="chat-bubble bg-gradient-to-r from-primary to-secondary text-primary-content shadow-md">{{ log.user_message }}</div>
              </div>
              <div v-if="log.ai_message" class="chat chat-start">
                <div class="chat-bubble bg-base-200 text-base-content shadow-sm prose max-w-none text-sm leading-relaxed" v-html="processBotMessage(log.ai_message).html"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Conversation list -->
        <div v-else class="bg-base-100 rounded-xl shadow-sm border border-base-200/50 overflow-hidden">
          <div class="divide-y divide-base-200/50">
            <div
              v-for="convo in conversations"
              :key="convo.conversation_id"
              @click="selectConversation(convo.conversation_id)"
              class="flex items-center justify-between p-6 cursor-pointer hover:bg-base-200/30 transition-all duration-300 group"
            >
              <div class="min-w-0 flex-1">
                <p class="font-bold text-lg text-base-content truncate group-hover:text-primary transition-colors pb-1">{{ convo.first_message || $t('chatLogs.noMessage') }}</p>
                <div class="flex gap-6 mt-2">
                  <span class="flex items-center gap-2 text-sm font-medium text-base-content/60 bg-base-200 px-3 py-1 rounded-full">
                    <font-awesome-icon :icon="['fas', 'comments']" class="text-primary/70" />
                    {{ convo.message_count }} Messages
                  </span>
                  <span class="flex items-center gap-2 text-sm font-medium text-base-content/60 bg-base-200 px-3 py-1 rounded-full">
                    <font-awesome-icon :icon="['fas', 'coins']" class="text-warning/70" />
                    CHF {{ (convo.total_cost || 0).toFixed(4) }}
                  </span>
                </div>
              </div>
              <div class="flex items-center gap-4 ml-6 shrink-0">
                <span class="text-sm font-semibold text-base-content/40 bg-base-200/50 px-3 py-1 rounded-lg">{{ new Date(convo.last_active).toLocaleString() }}</span>
                <div class="w-10 h-10 rounded-full bg-base-200 flex items-center justify-center group-hover:bg-primary group-hover:text-primary-content transition-colors">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="w-4 h-4" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
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

const activeTab = ref('analytics')

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
  } catch (err) {
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
      backgroundColor: 'rgba(10, 31, 171, 0.15)',
      borderColor: 'rgba(10, 31, 171, 1)',
      borderWidth: 3,
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
  responsive: true, maintainAspectRatio: false,
  scales: { y: { beginAtZero: true } },
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
  } catch (err) {
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
  if (tenant) { fetchAnalytics(); selectedConversation.value = null; conversations.value = [] }
}, { immediate: true })
</script>

<style scoped>
.chart-container { height: 400px; min-width: 100%; }
.chat-bubble { hyphens: auto; }
</style>
