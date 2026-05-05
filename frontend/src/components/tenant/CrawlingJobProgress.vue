<template>
  <div v-if="liveStatus === 'IN_PROGRESS'" class="crawl-progress">
    <div class="crawl-progress__header">
      <span>{{ progress.completed }} / {{ progress.total }} pages crawled</span>
      <span>{{ progressPercentage.toFixed(0) }}%</span>
    </div>
    <div class="crawl-progress__bar-track">
      <div class="crawl-progress__bar-fill" :style="{ width: progressPercentage + '%' }"></div>
    </div>
    <div class="crawl-progress__footer">
      <span class="crawl-progress__polling-label">Live · updating every 5s</span>
      <button @click="cancelJob" :disabled="cancelling" class="btn btn-xs btn-warning btn-outline gap-1">
        <font-awesome-icon v-if="cancelling" :icon="['fas', 'spinner']" class="animate-spin" />
        <font-awesome-icon v-else :icon="['fas', 'stop']" />
        {{ cancelling ? 'Stopping…' : 'Stop crawl' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, toRefs, onMounted, onUnmounted, computed } from 'vue';
import apiClient from '@/utils/api';
import { useToast } from '../../composables/useToast';

const props = defineProps({
  job:      { type: Object, required: true },
  tenantId: { type: String, required: true },
});
const { job, tenantId } = toRefs(props);
const emit = defineEmits(['job-completed', 'job-cancelled']);
const { addToast } = useToast();

const progress   = ref({ total: 0, completed: 0, pending: 0, in_progress: 0, failed: 0 });
const pollInterval = ref(null);
const cancelling = ref(false);
const liveStatus = ref(job.value.status);

const progressPercentage = computed(() => {
  if (!progress.value.total) return 0;
  return (progress.value.completed / progress.value.total) * 100;
});

const stopPolling = () => {
  if (pollInterval.value) { clearInterval(pollInterval.value); pollInterval.value = null; }
};

const fetchProgress = async () => {
  try {
    const r = await apiClient.get(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/progress`);
    progress.value = r.data;
    const done = r.data.total > 0 && r.data.pending === 0 && r.data.in_progress === 0;
    if (done) { liveStatus.value = 'COMPLETED'; stopPolling(); emit('job-completed', job.value.id); }
  } catch { stopPolling(); }
};

const cancelJob = async () => {
  if (cancelling.value) return;
  cancelling.value = true;
  stopPolling();
  try {
    await apiClient.post(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/cancel`);
    liveStatus.value = 'FAILED';
    addToast('Crawl stopped — already-indexed pages are kept.', 'success');
    emit('job-cancelled', job.value.id);
  } catch {
    addToast('Failed to stop the crawl.', 'error');
    pollInterval.value = setInterval(fetchProgress, 5000);
  } finally { cancelling.value = false; }
};

onMounted(() => {
  if (job.value.status === 'IN_PROGRESS') {
    fetchProgress();
    pollInterval.value = setInterval(fetchProgress, 5000);
  }
});
onUnmounted(stopPolling);
</script>
