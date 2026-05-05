<template>
    <div class="mt-2">
        <div class="flex justify-between text-sm font-medium text-base-content/70 mb-1">
            <span>{{ progress.completed }} / {{ progress.total }} pages</span>
            <span>{{ progressPercentage.toFixed(0) }}%</span>
        </div>
        <div class="w-full bg-base-300 rounded-full h-2.5">
            <div class="bg-success h-2.5 rounded-full transition-all duration-500" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <div v-if="job.status === 'IN_PROGRESS'" class="flex items-center justify-between mt-2">
            <span class="text-xs text-base-content/50 animate-pulse">Polling for updates…</span>
            <button
                @click="cancelJob"
                :disabled="cancelling"
                class="btn btn-xs btn-error btn-outline gap-1"
            >
                <font-awesome-icon v-if="cancelling" :icon="['fas', 'spinner']" class="animate-spin" />
                <font-awesome-icon v-else :icon="['fas', 'stop']" />
                {{ cancelling ? 'Cancelling…' : 'Cancel crawl' }}
            </button>
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
const emit = defineEmits(['job-completed', 'job-cancelled']);
const { addToast } = useToast();

const progress = ref({ total: 0, completed: 0, pending: 0, in_progress: 0, failed: 0 });
const pollInterval = ref(null);
const cancelling = ref(false);

const progressPercentage = computed(() => {
    if (progress.value.total === 0) return 0;
    return (progress.value.completed / progress.value.total) * 100;
});

const stopPolling = () => {
    if (pollInterval.value) {
        clearInterval(pollInterval.value);
        pollInterval.value = null;
    }
};

const fetchProgress = async () => {
    if (!tenantId.value || !job.value.id) return;
    try {
        const response = await apiClient.get(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/progress`);
        progress.value = response.data;

        const isDone = progress.value.total > 0
            && progress.value.pending === 0
            && progress.value.in_progress === 0;

        if (isDone || job.value.status === 'COMPLETED' || job.value.status === 'FAILED') {
            stopPolling();
            if (isDone || job.value.status === 'COMPLETED') {
                emit('job-completed', job.value.id);
            }
        }
    } catch (error) {
        addToast('Failed to fetch job progress.', 'error');
        console.error(`Failed to fetch progress for job ${job.value.id}:`, error);
        stopPolling();
    }
};

const cancelJob = async () => {
    if (cancelling.value) return;
    cancelling.value = true;
    stopPolling();
    try {
        await apiClient.post(`/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/cancel`);
        addToast('Crawl job cancelled.', 'success');
        emit('job-cancelled', job.value.id);
    } catch (error) {
        addToast('Failed to cancel the crawl job.', 'error');
        console.error('Cancel failed:', error);
        // Restart polling since cancel failed
        pollInterval.value = setInterval(fetchProgress, 5000);
    } finally {
        cancelling.value = false;
    }
};

onMounted(() => {
    fetchProgress();
    if (job.value.status === 'IN_PROGRESS') {
        pollInterval.value = setInterval(fetchProgress, 5000);
    }
});

onUnmounted(stopPolling);
</script>
