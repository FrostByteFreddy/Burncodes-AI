<template>
    <div class="mt-2">
        <div class="flex justify-between text-sm font-medium text-base-content/70 mb-1">
            <span>{{ progress.completed }} / {{ progress.total }} pages</span>
            <span>{{ progressPercentage.toFixed(0) }}%</span>
        </div>
        <div class="w-full bg-base-300 rounded-full h-2.5">
            <div class="bg-success h-2.5 rounded-full" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <div v-if="job.status === 'IN_PROGRESS'" class="text-xs text-center text-base-content/70 mt-1">
            Polling for updates...
        </div>
    </div>
</template>

<script setup>
import { ref, toRefs, onMounted, onUnmounted, computed, defineEmits } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../../stores/auth';
import { useToast } from '../../composables/useToast';

const props = defineProps({
    job: {
        type: Object,
        required: true
    },
    tenantId: {
        type: String,
        required: true
    }
});

const { job, tenantId } = toRefs(props);
const emit = defineEmits(['job-completed']);
const authStore = useAuthStore();
const { addToast } = useToast();
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const progress = ref({
    total: 0,
    completed: 0,
    pending: 0,
    in_progress: 0,
    failed: 0,
});
const pollInterval = ref(null);

const progressPercentage = computed(() => {
    if (progress.value.total === 0) return 0;
    return (progress.value.completed / progress.value.total) * 100;
});

const getAuthHeaders = () => {
    if (!authStore.session?.access_token) {
        throw new Error('User is not authenticated.');
    }
    return { Authorization: `Bearer ${authStore.session.access_token}` };
};

const fetchProgress = async () => {
    if (!tenantId.value || !job.value.id) return;
    try {
        const response = await axios.get(`${API_BASE_URL}/tenants/${tenantId.value}/crawling_jobs/${job.value.id}/progress`, { headers: getAuthHeaders() });
        progress.value = response.data;

        // If the job is completed or failed, stop polling
        if (job.value.status === 'COMPLETED' || job.value.status === 'FAILED') {
            if (pollInterval.value) {
                clearInterval(pollInterval.value);
                pollInterval.value = null;
                if (job.value.status === 'COMPLETED') {
                    emit('job-completed', job.value.id);
                }
            }
        }
    } catch (error) {
        addToast('Failed to fetch job progress.', 'error');
        console.error(`Failed to fetch progress for job ${job.value.id}:`, error);
        if (pollInterval.value) {
            clearInterval(pollInterval.value);
            pollInterval.value = null;
        }
    }
};

onMounted(() => {
    fetchProgress(); // Fetch immediately on mount
    // Only start polling if the job is in progress
    if (job.value.status === 'IN_PROGRESS') {
        pollInterval.value = setInterval(fetchProgress, 5000); // Poll every 5 seconds
    }
});

onUnmounted(() => {
    if (pollInterval.value) {
        clearInterval(pollInterval.value);
    }
});
</script>
