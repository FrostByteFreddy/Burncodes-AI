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
            <div v-for="job in crawlingJobs" :key="job.id" class="kl-job">

              <!-- Top row: badge + delete -->
              <div class="kl-job__topbar">
                <span class="kl-job__badge"
                  :class="{
                    'kl-job__badge--active': job.status === 'IN_PROGRESS',
                    'kl-job__badge--done':   job.status === 'COMPLETED',
                    'kl-job__badge--failed': job.status === 'FAILED',
                  }">
                  <span v-if="job.status === 'IN_PROGRESS'" class="live-dot"></span>
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

              <!-- URL + date -->
              <div class="kl-job__body">
                <p class="kl-job__url">{{ job.start_url }}</p>
                <p class="kl-job__meta">Started {{ fmtDate(job.created_at) }}</p>
              </div>

              <!-- Progress (live only) -->
              <CrawlingJobProgress
                :job="job"
                :tenantId="tenantsStore.currentTenant?.id"
                @job-completed="onJobCompleted(job.id)"
                @job-cancelled="onJobCancelled(job.id)"
              />

              <!-- Stats footer — only when there are sources -->
              <div v-if="job.sources && job.sources.length > 0" class="kl-job__footer">
                <!-- Segmented bar -->
                <div class="kl-page-bar">
                  <div class="kl-page-bar__ok"  :style="{ width: barWidth(job, 'ok') }"></div>
                  <div class="kl-page-bar__err" :style="{ width: barWidth(job, 'err') }"></div>
                </div>
                <!-- Stat row -->
                <div class="kl-job__stats-row">
                  <span class="kl-stat kl-stat--ok">
                    <font-awesome-icon :icon="['fas', 'circle-check']" />
                    {{ successCount(job) }} page{{ successCount(job) !== 1 ? 's' : '' }}
                  </span>
                  <span v-if="errorCount(job) > 0" class="kl-stat kl-stat--err">
                    <font-awesome-icon :icon="['fas', 'circle-xmark']" />
                    {{ errorCount(job) }} error{{ errorCount(job) !== 1 ? 's' : '' }}
                    <span class="kl-stat__breakdown">({{ errorBreakdown(job) }})</span>
                  </span>
                  <span class="kl-stats-spacer"></span>
                  <span class="kl-stat kl-stat--facts">
                    <font-awesome-icon :icon="['fas', 'bolt']" />
                    {{ factsCount(job).toLocaleString() }} Facts
                  </span>
                </div>
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
                        :                                 'status-dot--processing'">
                </span>
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
const showDeleteJobModal = ref(false);
const jobToDelete        = ref(null);

const hasActiveJob    = computed(() => props.crawlingJobs.some(j => j.status === 'IN_PROGRESS'));
const allTenantSources = computed(() => tenantsStore.currentTenant?.tenant_sources || []);
const fileSources      = computed(() => allTenantSources.value.filter(s => s.source_type === 'FILE'));

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
const barWidth = (job, type) => {
  const total = (job?.sources || []).length;
  if (!total) return '0%';
  return `${Math.round(((type === 'ok' ? successCount(job) : errorCount(job)) / total) * 100)}%`;
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
