<template>
  <div v-if="liveStatus === 'IN_PROGRESS'" class="crawl-progress">
    <div class="crawl-progress__bar-track">
      <div class="crawl-progress__bar-fill" :style="{ width: progressPercentage + '%' }"></div>
    </div>
    <span class="crawl-progress__label">
      {{ progress.completed }} / {{ progress.total }} pages · {{ progressPercentage.toFixed(0) }}%
      <span v-if="progress.failed > 0" class="crawl-progress__errors">
        · {{ progress.failed }} error{{ progress.failed !== 1 ? 's' : '' }}
      </span>
    </span>
  </div>
</template>

<script setup>
import { ref, toRefs, onMounted, onUnmounted, computed } from 'vue';
import apiClient from '@/utils/api';
import { supabase } from '@/supabase';
import { useToast } from '../../composables/useToast';

const props = defineProps({
  job:      { type: Object, required: true },
  tenantId: { type: String, required: true },
});
const { job, tenantId } = toRefs(props);
const emit = defineEmits(['job-completed', 'job-cancelled']);
const { addToast } = useToast();

const progress   = ref({ total: 0, completed: 0, pending: 0, in_progress: 0, failed: 0 });
const cancelling = ref(false);
const liveStatus = ref(job.value.status);

const progressPercentage = computed(() => {
  if (!progress.value.total) return 0;
  return (progress.value.completed / progress.value.total) * 100;
});

// ── Initial progress fetch (REST, one-shot) ────────────────────────────────
const fetchProgress = async () => {
  try {
    const r = await apiClient.get(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/progress`);
    progress.value = r.data;
    checkDone();
  } catch { /* ignore — realtime will keep us updated */ }
};

const checkDone = () => {
  const { total, pending, in_progress } = progress.value;
  if (total > 0 && pending === 0 && in_progress === 0) {
    liveStatus.value = 'COMPLETED';
    emit('job-completed', job.value.id);
  }
};

// ── Supabase Realtime on crawling_tasks for this job ──────────────────────
// We count task statuses locally to avoid a REST round-trip on every change.
let tasksChannel = null;

const subscribeToTasks = () => {
  tasksChannel = supabase
    .channel(`crawling-tasks-job-${job.value.id}`)
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'crawling_tasks',
        filter: `job_id=eq.${job.value.id}`,
      },
      () => {
        // Re-fetch aggregate counts from the API (cheap single-row query)
        fetchProgress();
      }
    )
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'crawling_tasks',
        filter: `job_id=eq.${job.value.id}`,
      },
      () => {
        // New tasks discovered — bump the total and re-fetch
        fetchProgress();
      }
    )
    .subscribe();
};

// ── Cancel ────────────────────────────────────────────────────────────────
const cancelJob = async () => {
  if (cancelling.value) return;
  cancelling.value = true;
  if (tasksChannel) supabase.removeChannel(tasksChannel);
  try {
    await apiClient.post(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/cancel`);
    liveStatus.value = 'FAILED';
    addToast('Crawl stopped — already-indexed pages are kept.', 'success');
    emit('job-cancelled', job.value.id);
  } catch {
    addToast('Failed to stop the crawl.', 'error');
    subscribeToTasks(); // re-subscribe if cancel failed
  } finally { cancelling.value = false; }
};

onMounted(() => {
  if (job.value.status === 'IN_PROGRESS') {
    fetchProgress();    // get current counts immediately
    subscribeToTasks(); // then listen for incremental updates
  }
});

onUnmounted(() => {
  if (tasksChannel) supabase.removeChannel(tasksChannel);
});
</script>
