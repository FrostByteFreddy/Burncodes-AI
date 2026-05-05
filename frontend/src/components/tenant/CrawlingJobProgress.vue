<template>
  <div class="crawl-progress">
    <div class="crawl-progress__header">
      <span>{{ progress.completed }} / {{ progress.total }} pages</span>
      <span>{{ progressPercentage.toFixed(0) }}%</span>
    </div>
    <div class="crawl-progress__bar-track">
      <div class="crawl-progress__bar-fill" :style="{ width: progressPercentage + '%' }"></div>
    </div>
    <div class="crawl-progress__footer">
      <span class="crawl-progress__polling-label">
        {{ liveStatus === 'IN_PROGRESS' ? 'Polling for updates…' : liveStatus }}
      </span>
      <div class="flex gap-2">
        <!-- Cancel: stops the crawl, keeps already-indexed data -->
        <button
          v-if="liveStatus === 'IN_PROGRESS'"
          @click="cancelJob"
          :disabled="cancelling || deleting"
          class="btn btn-xs btn-warning btn-outline gap-1"
        >
          <font-awesome-icon v-if="cancelling" :icon="['fas', 'spinner']" class="animate-spin" />
          <font-awesome-icon v-else :icon="['fas', 'stop']" />
          {{ cancelling ? 'Cancelling…' : 'Cancel' }}
        </button>
        <!-- Delete: cancels if running AND wipes all indexed data -->
        <button
          @click="deleteJob"
          :disabled="cancelling || deleting"
          class="btn btn-xs btn-error btn-outline gap-1"
        >
          <font-awesome-icon v-if="deleting" :icon="['fas', 'spinner']" class="animate-spin" />
          <font-awesome-icon v-else :icon="['fas', 'trash']" />
          {{ deleting ? 'Deleting…' : 'Delete' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, toRefs, onMounted, onUnmounted, computed } from 'vue';
import apiClient from '@/utils/api';
import { useToast } from '../../composables/useToast';

const props = defineProps({
  job: { type: Object, required: true },
  tenantId: { type: String, required: true }
});

const { job, tenantId } = toRefs(props);
const emit = defineEmits(['job-completed', 'job-cancelled', 'job-deleted']);
const { addToast } = useToast();

const progress = ref({ total: 0, completed: 0, pending: 0, in_progress: 0, failed: 0 });
const pollInterval = ref(null);
const cancelling = ref(false);
const deleting = ref(false);
// Track live status locally so the UI reacts without waiting for parent re-render
const liveStatus = ref(job.value.status);

const progressPercentage = computed(() => {
  if (progress.value.total === 0) return 0;
  return (progress.value.completed / progress.value.total) * 100;
});

const stopPolling = () => {
  if (pollInterval.value) { clearInterval(pollInterval.value); pollInterval.value = null; }
};

const fetchProgress = async () => {
  if (!tenantId.value || !job.value.id) return;
  try {
    const response = await apiClient.get(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/progress`);
    progress.value = response.data;
    const isDone = progress.value.total > 0 && progress.value.pending === 0 && progress.value.in_progress === 0;
    if (isDone || liveStatus.value === 'COMPLETED') {
      liveStatus.value = 'COMPLETED';
      stopPolling();
      emit('job-completed', job.value.id);
    }
  } catch (error) {
    addToast('Failed to fetch job progress.', 'error');
    console.error(`Failed to fetch progress for job ${job.value.id}:`, error);
    stopPolling();
  }
};

const cancelJob = async () => {
  if (cancelling.value || deleting.value) return;
  cancelling.value = true;
  stopPolling();
  try {
    await apiClient.post(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/cancel`);
    liveStatus.value = 'FAILED';
    addToast('Crawl cancelled — already-indexed pages are kept.', 'success');
    emit('job-cancelled', job.value.id);
  } catch (error) {
    addToast('Failed to cancel the crawl job.', 'error');
    console.error('Cancel failed:', error);
    // Resume polling since cancel didn't succeed
    pollInterval.value = setInterval(fetchProgress, 5000);
  } finally {
    cancelling.value = false;
  }
};

const deleteJob = async () => {
  if (cancelling.value || deleting.value) return;
  deleting.value = true;
  stopPolling();
  try {
    await apiClient.delete(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}`);
    addToast('Crawl job and all indexed data deleted.', 'success');
    emit('job-deleted', job.value.id);
  } catch (error) {
    addToast('Failed to delete the crawl job.', 'error');
    console.error('Delete failed:', error);
  } finally {
    deleting.value = false;
  }
};

onMounted(() => {
  fetchProgress();
  if (job.value.status === 'IN_PROGRESS') pollInterval.value = setInterval(fetchProgress, 5000);
});

onUnmounted(stopPolling);
</script>
