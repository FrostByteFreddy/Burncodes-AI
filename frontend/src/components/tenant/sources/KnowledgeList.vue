<template>
  <div class="knowledge-list">
    <div v-if="tenantsStore.loading" class="kl-skeleton">
      <div v-for="n in 3" :key="n" class="skeleton-row"></div>
    </div>

    <div v-else class="kl-body">

      <!-- ── LEFT: Crawl Jobs ──────────────────────────── -->
      <div class="kl-col-main">
        <div v-if="crawlingJobs.length > 0" class="kl-section">
          <h3 class="kl-section__title">
            <span v-if="hasActiveJob" class="live-dot"></span>
            Crawl Jobs
          </h3>

          <div class="kl-jobs">
            <div v-for="job in crawlingJobs" :key="job.id" class="kl-job-row">

              <!-- Icon -->
              <div class="kl-job-row__icon">
                <font-awesome-icon :icon="['fas', 'globe']" />
              </div>

              <!-- Info -->
              <div class="kl-job-row__info">
                <p class="kl-job-row__url">{{ job.start_url }}</p>
                <p class="kl-job-row__meta">
                  Started {{ fmtDate(job.created_at) }}
                  <template v-if="job.sources && job.sources.length > 0">
                    &middot; {{ successCount(job) }} page{{ successCount(job) !== 1 ? 's' : '' }}
                    &middot; {{ factsCount(job).toLocaleString() }} facts
                    <span v-if="errorCount(job) > 0" class="kl-job-row__errors">
                      &middot; {{ errorCount(job) }} error{{ errorCount(job) !== 1 ? 's' : '' }}
                      <span class="kl-job-row__breakdown">({{ errorBreakdown(job) }})</span>
                    </span>
                  </template>
                </p>

                <!-- Inline progress — only renders when IN_PROGRESS -->
                <CrawlingJobProgress
                  :job="job"
                  :tenantId="tenantsStore.currentTenant?.id"
                  @job-completed="onJobCompleted(job.id)"
                  @job-cancelled="onJobCancelled(job.id)"
                />
              </div>

              <!-- Status badge + actions -->
              <div class="kl-job-row__actions">
                <!-- Stop — only visible while IN_PROGRESS -->
                <button
                  v-if="job.status === 'IN_PROGRESS'"
                  @click="stopJob(job)"
                  :disabled="stoppingJobId === job.id"
                  class="kl-job-row__stop"
                  title="Stop crawl"
                >
                  <font-awesome-icon v-if="stoppingJobId === job.id" :icon="['fas', 'spinner']" class="animate-spin" />
                  <font-awesome-icon v-else :icon="['fas', 'stop']" />
                  {{ stoppingJobId === job.id ? 'Stopping…' : 'Stop' }}
                </button>

                <!-- Delete -->
                <button
                  @click="confirmDeleteJob(job)"
                  :disabled="deletingJobId === job.id"
                  class="kl-job-row__delete"
                  title="Delete job and all indexed data"
                >
                  <font-awesome-icon v-if="deletingJobId === job.id" :icon="['fas', 'spinner']" class="animate-spin" />
                  <font-awesome-icon v-else :icon="['fas', 'trash-alt']" />
                </button>
              </div>

            </div>
          </div>
        </div>

        <div v-if="crawlingJobs.length === 0 && fileSources.length === 0" class="kl-empty">
          <font-awesome-icon :icon="['fas', 'database']" />
          <p>No knowledge sources yet.<br>Add a website or document above.</p>
        </div>
      </div>

      <!-- ── RIGHT: Documents sidebar ─────────────────── -->
      <aside v-if="fileSources.length > 0" class="kl-col-aside">
        <h3 class="kl-section__title">Documents</h3>
        <div class="kl-doc-list">
          <div v-for="source in fileSources" :key="source.id" class="kl-doc-row">
            <div class="kl-doc-row__icon" :class="`kl-doc-row__icon--${fileExt(source)}`">
              <font-awesome-icon :icon="['fas', fileIcon(source)]" />
            </div>
            <div class="kl-doc-row__info">
              <p class="kl-doc-row__name" :title="fileName(source)">{{ fileName(source) }}</p>
              <p class="kl-doc-row__meta">
                <span class="status-dot"
                  :class="source.status === 'COMPLETED' ? 'status-dot--success'
                        : source.status === 'ERROR'     ? 'status-dot--error'
                        :                                 'status-dot--processing'"
                ></span>
                {{ fileExt(source).toUpperCase() }}
              </p>
            </div>
            <button @click="$emit('delete-source', source)" class="kl-doc-row__delete" title="Delete document">
              <font-awesome-icon :icon="['fas', 'trash-alt']" />
            </button>
          </div>
        </div>
      </aside>

    </div>

    <ConfirmationModal
      :show="showDeleteJobModal"
      title="Delete Crawl Job"
      :message="`Delete the crawl of <strong>${jobToDelete?.start_url}</strong>?<br><br>${jobToDelete?.task_count || 0} pages attempted · ${successCount(jobToDelete)} indexed · ${errorCount(jobToDelete)} errors.<br>All indexed data will be removed. This cannot be undone.`"
      confirmButtonText="Delete"
      @confirm="executeDeleteJob"
      @cancel="jobToDelete = null; showDeleteJobModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
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

const deletingJobId      = ref(null);
const stoppingJobId      = ref(null);
const showDeleteJobModal = ref(false);
const jobToDelete        = ref(null);

const hasActiveJob    = computed(() => props.crawlingJobs.some(j => j.status === 'IN_PROGRESS'));
const allTenantSources = computed(() => tenantsStore.currentTenant?.tenant_sources || []);
const fileSources      = computed(() => allTenantSources.value.filter(s => s.source_type === 'FILE'));

const stopJob = async (job) => {
  if (stoppingJobId.value) return;
  stoppingJobId.value = job.id;
  try {
    await apiClient.post(`/tenants/${tenantsStore.currentTenant.id}/crawling_jobs/${job.id}/cancel`);
    addToast('Crawl stopped — already-indexed pages are kept.', 'success');
    emit('job-cancelled', job.id);
  } catch {
    addToast('Failed to stop the crawl.', 'error');
  } finally {
    stoppingJobId.value = null;
  }
};

// ── File helpers ──────────────────────────────────────
const fileName = (s) => s.source_location.split('/').pop().split('?')[0] || s.source_location;
const fileExt  = (s) => { const n = fileName(s); return n.includes('.') ? n.split('.').pop().toLowerCase() : 'file'; };
const fileIcon = (s) => {
  const e = fileExt(s);
  if (e === 'pdf')                       return 'file-pdf';
  if (['doc','docx'].includes(e))        return 'file-word';
  if (['xls','xlsx'].includes(e))        return 'file-excel';
  if (['ppt','pptx'].includes(e))        return 'file-powerpoint';
  if (['txt','md'].includes(e))          return 'file-lines';
  if (e === 'csv')                       return 'file-csv';
  if (['zip','tar','gz'].includes(e))    return 'file-zipper';
  return 'file';
};

// ── Job stat helpers ──────────────────────────────────
const successCount   = (job) => (job?.sources || []).filter(s => s.status === 'COMPLETED').length;
const errorCount     = (job) => (job?.sources || []).filter(s => s.status === 'ERROR').length;
const factsCount     = (job) => (job?.sources || []).reduce((sum, s) => sum + (s.chunk_count || 0), 0);
const errorBreakdown = (job) => {
  const codes = {};
  (job?.sources || []).filter(s => s.status === 'ERROR').forEach(s => {
    const c = s.status_code || '?'; codes[c] = (codes[c] || 0) + 1;
  });
  return Object.entries(codes).map(([c, n]) => `${n}× ${c}`).join(', ');
};

const fmtDate = (iso) => new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

const onJobCompleted = (id) => emit('job-completed', id);
const onJobCancelled = (id) => emit('job-cancelled', id);

const confirmDeleteJob = (job) => { jobToDelete.value = job; showDeleteJobModal.value = true; };
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
