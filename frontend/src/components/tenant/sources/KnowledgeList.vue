<template>
  <div class="knowledge-list">
    <!-- Loading skeleton -->
    <div v-if="tenantsStore.loading" class="kl-skeleton">
      <div v-for="n in 3" :key="n" class="skeleton-row"></div>
    </div>

    <div v-else>
      <!-- ── Crawl Jobs ─────────────────────────────────── -->
      <div v-if="crawlingJobs.length > 0" class="kl-section">
        <h3 class="kl-section__title">
          <span v-if="hasActiveJob" class="live-dot"></span>
          Crawl Jobs
        </h3>

        <div class="kl-jobs">
          <div v-for="job in crawlingJobs" :key="job.id" class="kl-job">

            <!-- Job header -->
            <div class="kl-job__header">
              <div class="kl-job__status-strip"
                :class="{
                  'kl-job__status-strip--active':    job.status === 'IN_PROGRESS',
                  'kl-job__status-strip--done':      job.status === 'COMPLETED',
                  'kl-job__status-strip--failed':    job.status === 'FAILED',
                }">
              </div>
              <div class="kl-job__info">
                <p class="kl-job__url">{{ job.start_url }}</p>
                <p class="kl-job__meta">
                  {{ job.task_count || 0 }} pages · {{ fmtDate(job.created_at) }}
                </p>
              </div>
              <div class="kl-job__actions">
                <span class="kl-job__badge"
                  :class="{
                    'kl-job__badge--active':  job.status === 'IN_PROGRESS',
                    'kl-job__badge--done':    job.status === 'COMPLETED',
                    'kl-job__badge--failed':  job.status === 'FAILED',
                  }">
                  {{ job.status === 'IN_PROGRESS' ? 'Live' : job.status === 'COMPLETED' ? 'Done' : 'Stopped' }}
                </span>
                <button
                  @click="confirmDeleteJob(job)"
                  :disabled="deletingJobId === job.id"
                  class="kl-job__delete-btn"
                  title="Delete job and all indexed data"
                >
                  <font-awesome-icon v-if="deletingJobId === job.id" :icon="['fas', 'spinner']" class="animate-spin" />
                  <font-awesome-icon v-else :icon="['fas', 'trash-alt']" />
                </button>
              </div>
            </div>

            <!-- Progress bar (only when live) -->
            <CrawlingJobProgress
              :job="job"
              :tenantId="tenantsStore.currentTenant?.id"
              @job-completed="onJobCompleted(job.id)"
              @job-cancelled="onJobCancelled(job.id)"
            />

            <!-- Sources for this job -->
            <div v-if="job.sources && job.sources.length > 0" class="kl-job__sources">
              <div
                v-for="(source, i) in visibleSources(job)"
                :key="source.id"
                class="kl-source-row"
              >
                <span class="status-dot"
                  :class="source.status === 'COMPLETED' ? 'status-dot--success' : source.status === 'ERROR' ? 'status-dot--error' : 'status-dot--processing'">
                </span>
                <span class="kl-source-row__url" :title="source.source_location">{{ source.source_location }}</span>
                <span class="kl-source-row__code" v-if="source.status_code">{{ source.status_code }}</span>
              </div>
              <button
                v-if="job.sources.length > PREVIEW_LIMIT"
                class="kl-job__expand-btn"
                @click="toggleExpanded(job.id)"
              >
                <font-awesome-icon :icon="['fas', expandedJobs.has(job.id) ? 'chevron-up' : 'chevron-down']" />
                {{ expandedJobs.has(job.id) ? 'Show less' : `+ ${job.sources.length - PREVIEW_LIMIT} more pages` }}
              </button>
            </div>
            <div v-else-if="job.status !== 'IN_PROGRESS'" class="kl-job__empty">
              No pages indexed yet.
            </div>

          </div>
        </div>
      </div>

      <!-- ── Standalone Files ──────────────────────────── -->
      <div v-if="fileSources.length > 0" class="kl-section">
        <h3 class="kl-section__title">{{ $t('tenant.sources.existing.uploadedFiles') }}</h3>
        <div class="kl-source-list">
          <div v-for="source in fileSources" :key="source.id" class="source-item">
            <div class="source-item__body">
              <p class="source-item__name">
                <font-awesome-icon :icon="['fas', 'file-pdf']" class="text-primary/60" />
                {{ source.source_location.split('/').pop() }}
              </p>
              <p class="source-item__meta">
                <span class="status-dot" :class="source.status === 'COMPLETED' ? 'status-dot--success' : source.status === 'ERROR' ? 'status-dot--error' : 'status-dot--processing'"></span>
                {{ source.status }}
              </p>
            </div>
            <button @click="$emit('delete-source', source)" class="source-item__delete">
              <font-awesome-icon :icon="['fas', 'times']" />
            </button>
          </div>
        </div>
      </div>

      <!-- ── Standalone URLs (not part of any job) ─────── -->
      <div v-if="standaloneUrlSources.length > 0" class="kl-section">
        <h3 class="kl-section__title">{{ $t('tenant.sources.existing.crawledUrls') }}</h3>
        <div class="kl-source-list">
          <div v-for="source in standaloneUrlSources" :key="source.id" class="source-item">
            <div class="source-item__body">
              <p class="source-item__name">
                <font-awesome-icon :icon="['fas', 'globe']" class="text-secondary/60" />
                {{ source.source_location }}
              </p>
              <p class="source-item__meta">
                <span class="status-dot" :class="source.status === 'COMPLETED' ? 'status-dot--success' : source.status === 'ERROR' ? 'status-dot--error' : 'status-dot--processing'"></span>
                {{ source.status }}
              </p>
            </div>
            <button @click="$emit('delete-source', source)" class="source-item__delete">
              <font-awesome-icon :icon="['fas', 'times']" />
            </button>
          </div>
        </div>
      </div>

      <!-- ── Empty state ─────────────────────────────────── -->
      <div v-if="crawlingJobs.length === 0 && fileSources.length === 0 && standaloneUrlSources.length === 0" class="kl-empty">
        <font-awesome-icon :icon="['fas', 'database']" class="text-4xl text-base-content/20 mb-4" />
        <p class="text-base-content/50 text-sm">No knowledge sources yet. Add a website or document above.</p>
      </div>
    </div>

    <!-- Confirm delete job modal -->
    <ConfirmationModal
      :show="showDeleteJobModal"
      title="Delete Crawl Job"
      :message="`Delete the crawl of <strong>${jobToDelete?.start_url}</strong> and all ${jobToDelete?.sources?.length || 0} indexed pages? This cannot be undone.`"
      confirmButtonText="Delete"
      @confirm="executeDeleteJob"
      @cancel="jobToDelete = null; showDeleteJobModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue';
import { useTenantsStore } from '../../../stores/tenants';
import { useToast } from '../../../composables/useToast';
import apiClient from '@/utils/api';
import CrawlingJobProgress from '../CrawlingJobProgress.vue';
import ConfirmationModal from '../../ConfirmationModal.vue';

const props = defineProps({
  crawlingJobs: { type: Array, default: () => [] },
});
const emit = defineEmits(['delete-source', 'job-completed', 'job-cancelled', 'job-deleted']);

const tenantsStore = useTenantsStore();
const { addToast }  = useToast();

const PREVIEW_LIMIT   = 5;
const expandedJobs    = reactive(new Set());
const deletingJobId   = ref(null);
const showDeleteJobModal = ref(false);
const jobToDelete     = ref(null);

// ── Computed ──────────────────────────────────────────
const hasActiveJob = computed(() => props.crawlingJobs.some(j => j.status === 'IN_PROGRESS'));

// IDs of all sources that belong to a crawl job
const jobSourceIds = computed(() => {
  const ids = new Set();
  for (const job of props.crawlingJobs)
    for (const s of (job.sources || [])) ids.add(s.id);
  return ids;
});

const allTenantSources = computed(() => tenantsStore.currentTenant?.tenant_sources || []);

const fileSources = computed(() =>
  allTenantSources.value.filter(s => s.source_type === 'FILE')
);

const standaloneUrlSources = computed(() =>
  allTenantSources.value.filter(s => s.source_type === 'URL' && !jobSourceIds.value.has(s.id))
);

// ── Helpers ───────────────────────────────────────────
const fmtDate = (iso) => new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

const visibleSources = (job) =>
  expandedJobs.has(job.id) ? job.sources : job.sources.slice(0, PREVIEW_LIMIT);

const toggleExpanded = (jobId) => {
  if (expandedJobs.has(jobId)) expandedJobs.delete(jobId);
  else expandedJobs.add(jobId);
};

// ── Job events ────────────────────────────────────────
const onJobCompleted = (id) => emit('job-completed', id);
const onJobCancelled = (id) => emit('job-cancelled', id);

// ── Delete job ────────────────────────────────────────
const confirmDeleteJob = (job) => {
  jobToDelete.value = job;
  showDeleteJobModal.value = true;
};

const executeDeleteJob = async () => {
  if (!jobToDelete.value) return;
  const job = jobToDelete.value;
  showDeleteJobModal.value = false;
  jobToDelete.value = null;
  deletingJobId.value = job.id;
  try {
    await apiClient.delete(`/tenants/${tenantsStore.currentTenant.id}/crawling_jobs/${job.id}`);
    addToast('Crawl job and all indexed data deleted.', 'success');
    emit('job-deleted', job.id);
  } catch {
    addToast('Failed to delete the crawl job.', 'error');
  } finally {
    deletingJobId.value = null;
  }
};
</script>
