<template>
  <div class="sources-page">

    <!-- ── Overview ─────────────────────────────────────────── -->
    <div class="kstats">
      <div v-for="s in stats" :key="s.label" class="kstat">
        <p class="kstat__label">{{ s.label }}</p>
        <p class="kstat__value">{{ s.value }}</p>
      </div>
    </div>

    <!-- ── Crawls ───────────────────────────────────────────── -->
    <section class="knowledge-panel">
      <div class="knowledge-panel__header">
        <div class="knowledge-panel__header-left">
          <div class="knowledge-panel__icon">
            <font-awesome-icon :icon="['fas', 'globe']" />
          </div>
          <div>
            <h2 class="knowledge-panel__title">{{ $t('knowledge.crawls.title') }}</h2>
            <p class="knowledge-panel__sub">{{ $t('knowledge.crawls.sub') }}</p>
          </div>
        </div>
        <button @click="wizardOpen = true" class="panel-add-btn" :title="$t('tenant.sources.wizard.addKnowledge')" :aria-label="$t('tenant.sources.wizard.addKnowledge')">
          <font-awesome-icon :icon="['fas', 'plus']" />
        </button>
      </div>

      <div class="knowledge-panel__divider"></div>

      <div v-if="shownJobs.length" class="kjobs">
        <CrawlJobCard
          v-for="(job, i) in shownJobs"
          :key="job.id"
          :job="job"
          :tenant-id="tenantId"
          :log="logsByJob[job.id] || []"
          :expanded="i === 0 && job.status === 'COMPLETED'"
          @confirmed="onJobChanged"
          @stop="stopJob"
          @delete="askDeleteJob"
        />
        <button v-if="crawlingJobs.length > JOBS_SHOWN" class="kjobs__more" @click="showAllJobs = !showAllJobs">
          {{ showAllJobs ? $t('knowledge.crawls.showLess') : $t('knowledge.crawls.showAll', { n: crawlingJobs.length }) }}
        </button>
      </div>
      <p v-else class="kempty">{{ $t('knowledge.crawls.empty') }}</p>
    </section>

    <!-- ── Website content ──────────────────────────────────── -->
    <section v-if="webSources.length" class="knowledge-panel">
      <div class="knowledge-panel__header knowledge-panel__header--solo">
        <div class="knowledge-panel__header-left">
          <div class="knowledge-panel__icon">
            <font-awesome-icon :icon="['fas', 'sitemap']" />
          </div>
          <div>
            <h2 class="knowledge-panel__title">{{ $t('knowledge.content.title') }}</h2>
            <p class="knowledge-panel__sub">{{ $t('knowledge.content.sub') }}</p>
          </div>
        </div>
      </div>
      <div class="knowledge-panel__divider"></div>
      <PageTree :sources="webSources" />
    </section>

    <!-- ── Uploaded files ───────────────────────────────────── -->
    <section class="knowledge-panel">
      <div class="knowledge-panel__header">
        <div class="knowledge-panel__header-left">
          <div class="knowledge-panel__icon knowledge-panel__icon--accent">
            <font-awesome-icon :icon="['fas', 'file-arrow-up']" />
          </div>
          <div>
            <h2 class="knowledge-panel__title">{{ $t('knowledge.files.title') }}</h2>
            <p class="knowledge-panel__sub">{{ $t('knowledge.files.sub') }}</p>
          </div>
        </div>
        <button @click="wizardOpen = true" class="panel-add-btn panel-add-btn--accent" :title="$t('knowledge.files.upload')" :aria-label="$t('knowledge.files.upload')">
          <font-awesome-icon :icon="['fas', 'plus']" />
        </button>
      </div>
      <div class="knowledge-panel__divider"></div>

      <div v-if="fileSources.length" class="kfiles">
        <div v-for="source in fileSources" :key="source.id" class="kfile">
          <span class="kfile__icon"><font-awesome-icon :icon="['fas', fileIcon(source)]" /></span>
          <div class="kfile__info">
            <p class="kfile__name" :title="source.summary || fileName(source)">{{ source.title && source.title !== fileName(source) ? source.title : fileName(source) }}</p>
            <p class="kfile__meta">
              {{ fileExt(source).toUpperCase() }}
              <template v-if="source.indexed_chunks != null"> · {{ source.indexed_chunks }} {{ $t('knowledge.tree.chunks') }}</template>
              · <span :class="`kfile__status kfile__status--${source.status.toLowerCase()}`">{{ $t(`knowledge.tree.status.${source.status}`) }}</span>
            </p>
          </div>
          <button @click="confirmDelete(source)" class="kfile__delete" :title="$t('tenant.sources.deleteModal.confirm')" :aria-label="$t('tenant.sources.deleteModal.confirm')">
            <font-awesome-icon :icon="['fas', 'trash-alt']" />
          </button>
        </div>
      </div>
      <p v-else class="kempty">{{ $t('knowledge.files.empty') }}</p>
    </section>

    <!-- ── Custom knowledge (fine-tuning rules) ─────────────── -->
    <section class="knowledge-panel">
      <div class="knowledge-panel__header">
        <div class="knowledge-panel__header-left">
          <div class="knowledge-panel__icon knowledge-panel__icon--accent">
            <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" />
          </div>
          <div>
            <h2 class="knowledge-panel__title">Custom Knowledge</h2>
            <p class="knowledge-panel__sub">Fine-tuning rules that guide how the bot responds to specific triggers</p>
          </div>
        </div>
        <button @click="rulesTabRef?.openModal()" class="panel-add-btn panel-add-btn--accent" title="Add rule" aria-label="Add rule">
          <font-awesome-icon :icon="['fas', 'plus']" />
        </button>
      </div>
      <div class="knowledge-panel__divider"></div>
      <RulesTab ref="rulesTabRef" />
    </section>

    <AddKnowledgeWizard
      :open="wizardOpen"
      @close="wizardOpen = false"
      @crawl-started="onJobChanged"
      @upload-done="refreshSources"
    />

    <ConfirmationModal
      :show="showConfirmationModal"
      :title="$t('tenant.sources.deleteModal.title')"
      :message="$t('tenant.sources.deleteModal.message', { source: escapeHtml(fileName(sourceToDelete || {})) })"
      :confirmButtonText="$t('tenant.sources.deleteModal.confirm')"
      @confirm="handleDelete"
      @cancel="cancelDelete"
    />

    <ConfirmationModal
      :show="!!jobToDelete"
      :title="$t('knowledge.deleteJob.title')"
      :message="$t('knowledge.deleteJob.message', { url: escapeHtml(jobToDelete?.start_url) })"
      :confirmButtonText="$t('tenant.sources.deleteModal.confirm')"
      @confirm="executeDeleteJob"
      @cancel="jobToDelete = null"
    />
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import apiClient from '@/utils/api';
import { supabase } from '@/supabase';
import { escapeHtml } from '@/utils/escapeHtml';
import AddKnowledgeWizard from './sources/AddKnowledgeWizard.vue';
import CrawlJobCard from './sources/CrawlJobCard.vue';
import PageTree from './sources/PageTree.vue';
import ConfirmationModal from '../ConfirmationModal.vue';
import RulesTab from './sources/RulesTab.vue';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t, locale } = useI18n();

const JOBS_SHOWN = 4;
const ACTIVE = ['IN_PROGRESS', 'SCANNED', 'INDEXING'];
const POLL_MS = 5000;

const wizardOpen            = ref(false);
const crawlingJobs          = ref([]);
const logsByJob             = ref({});
const showAllJobs           = ref(false);
const sourceToDelete        = ref(null);
const showConfirmationModal = ref(false);
const jobToDelete           = ref(null);
const rulesTabRef           = ref(null);

const tenantId = computed(() => tenantsStore.currentTenant?.id || '');
const allSources = computed(() => tenantsStore.currentTenant?.tenant_sources || []);
const webSources = computed(() => allSources.value.filter((s) => s.source_type === 'URL' || s.source_type === 'FILE_URL'));
const fileSources = computed(() => allSources.value.filter((s) => s.source_type === 'FILE'));
const shownJobs = computed(() => (showAllJobs.value ? crawlingJobs.value : crawlingJobs.value.slice(0, JOBS_SHOWN)));
const hasActiveJob = computed(() => crawlingJobs.value.some((j) => ACTIVE.includes(j.status)));

// ── Overview numbers (each URL once — older crawls stored duplicates) ──
const stats = computed(() => {
  const unique = new Map();
  for (const s of allSources.value) unique.set(`${s.source_type}:${s.source_location}`, s);
  const rows = [...unique.values()];
  const learned = rows.filter((s) => s.status === 'COMPLETED');
  const lastCrawl = crawlingJobs.value[0]?.created_at;
  return [
    { label: t('knowledge.stats.pages'), value: learned.filter((s) => s.source_type === 'URL').length.toLocaleString(locale.value) },
    { label: t('knowledge.stats.files'), value: learned.filter((s) => s.source_type !== 'URL').length.toLocaleString(locale.value) },
    { label: t('knowledge.stats.chunks'), value: learned.reduce((n, s) => n + (s.indexed_chunks || 0), 0).toLocaleString(locale.value) },
    {
      label: t('knowledge.stats.lastCrawl'),
      value: lastCrawl ? new Date(lastCrawl).toLocaleDateString(locale.value, { day: '2-digit', month: '2-digit', year: 'numeric' }) : t('knowledge.stats.never'),
    },
  ];
});

// ── Data ───────────────────────────────────────────────────────────────
const fetchCrawlingJobs = async () => {
  if (!tenantId.value) return;
  try {
    const r = await apiClient.get(`/tenants/${tenantId.value}/crawling_jobs`);
    crawlingJobs.value = r.data;
  } catch { addToast(t('tenant.sources.actions.fetchFailed'), 'error'); }
};

const fetchLog = async (jobId) => {
  try {
    const r = await apiClient.get(`/tenants/${tenantId.value}/crawling_jobs/${jobId}/log`, { params: { limit: 200 } });
    logsByJob.value = { ...logsByJob.value, [jobId]: r.data };
  } catch { /* the log is a nice-to-have */ }
};

// Logs of running jobs (and the newest one) are loaded once; Realtime appends.
const loadLogs = async () => {
  const wanted = crawlingJobs.value.filter((j, i) => ACTIVE.includes(j.status) || i === 0);
  await Promise.all(wanted.filter((j) => !logsByJob.value[j.id]).map((j) => fetchLog(j.id)));
};

const refreshSources = async () => { if (tenantId.value) await tenantsStore.refetch(tenantId.value); };

// Coalesce bursts of events into one refresh
let refreshTimer = null;
const scheduleRefresh = ({ sources = false } = {}) => {
  if (sources) scheduleRefresh.sources = true;
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(async () => {
    const withSources = scheduleRefresh.sources;
    scheduleRefresh.sources = false;
    await fetchCrawlingJobs();
    if (withSources) await refreshSources();
  }, 1200);
};

// ── Realtime: job status + activity log ─────────────────────────────────
let channel = null;
const subscribe = (id) => {
  if (channel) { supabase.removeChannel(channel); channel = null; }
  if (!id) return;
  channel = supabase
    .channel(`knowledge-${id}`)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'crawling_jobs', filter: `tenant_id=eq.${id}` }, (payload) => {
      const before = payload.old?.status;
      const after = payload.new?.status;
      if (payload.eventType === 'UPDATE' && after !== before) {
        if (after === 'SCANNED') addToast(t('tenant.sources.actions.scanCompleted'), 'info');
        if (after === 'COMPLETED') addToast(t('tenant.sources.actions.crawlCompleted'), 'success');
      }
      scheduleRefresh({ sources: after === 'COMPLETED' });
    })
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'crawl_job_log', filter: `tenant_id=eq.${id}` }, (payload) => {
      const entry = payload.new;
      const current = logsByJob.value[entry.job_id] || [];
      if (current.some((e) => e.id === entry.id)) return;
      logsByJob.value = { ...logsByJob.value, [entry.job_id]: [...current, entry] };
      // learned/scanned items change the page tree and counters
      scheduleRefresh({ sources: ['learned', 'learn_failed', 'scanned', 'job_done'].includes(entry.event) });
    })
    .subscribe();
};

// Keyed on the id: the store replaces currentTenant on every refetch, and
// re-subscribing each time dropped events in between.
watch(tenantId, async (id) => {
  crawlingJobs.value = [];
  logsByJob.value = {};
  subscribe(id);
  if (id) {
    await fetchCrawlingJobs();
    await loadLogs();
  }
}, { immediate: true });

// Safety net while something runs: Realtime can drop events (tab asleep,
// network change). Polling keeps progress moving regardless.
let pollTimer = null;
watch(hasActiveJob, (active) => {
  clearInterval(pollTimer);
  if (active) {
    pollTimer = setInterval(async () => {
      await fetchCrawlingJobs();
      await loadLogs();
      if (crawlingJobs.value.some((j) => j.status === 'INDEXING')) await refreshSources();
    }, POLL_MS);
  }
}, { immediate: true });
watch(() => crawlingJobs.value.map((j) => `${j.id}:${j.status}`).join(), loadLogs);

onUnmounted(() => {
  if (channel) supabase.removeChannel(channel);
  clearInterval(pollTimer);
  clearTimeout(refreshTimer);
});

// ── Actions ────────────────────────────────────────────────────────────
const onJobChanged = async () => {
  await fetchCrawlingJobs();
  await loadLogs();
};

const stopJob = async (job) => {
  try {
    await apiClient.post(`/tenants/${tenantId.value}/crawling_jobs/${job.id}/cancel`);
    await fetchCrawlingJobs();
  } catch { addToast(t('tenant.sources.actions.fetchFailed'), 'error'); }
};

const askDeleteJob = (job) => { jobToDelete.value = job; };
const executeDeleteJob = async () => {
  const job = jobToDelete.value;
  jobToDelete.value = null;
  if (!job) return;
  try {
    await apiClient.delete(`/tenants/${tenantId.value}/crawling_jobs/${job.id}`);
    await fetchCrawlingJobs();
    await refreshSources();
  } catch { addToast(t('tenant.sources.actions.deleteFailed'), 'error'); }
};

// ── Uploaded files ─────────────────────────────────────────────────────
const fileName = (s) => (s.source_location || '').split('/').pop().split('?')[0].replace(/^[0-9a-f]{32}_/, '');
const fileExt = (s) => { const n = fileName(s); return n.includes('.') ? n.split('.').pop().toLowerCase() : 'file'; };
const FILE_ICONS = { pdf: 'file-pdf', doc: 'file-word', docx: 'file-word', xls: 'file-excel', xlsx: 'file-excel',
  ppt: 'file-powerpoint', pptx: 'file-powerpoint', txt: 'file-lines', md: 'file-lines', csv: 'file-csv' };
const fileIcon = (s) => FILE_ICONS[fileExt(s)] || 'file';

const confirmDelete = (source) => { sourceToDelete.value = source; showConfirmationModal.value = true; };
const cancelDelete = () => { sourceToDelete.value = null; showConfirmationModal.value = false; };
const handleDelete = async () => {
  if (!sourceToDelete.value) return;
  const id = sourceToDelete.value.id;
  try {
    await apiClient.delete(`/tenants/${tenantId.value}/sources/${id}`);
    addToast(t('tenant.sources.actions.deleteSuccess'), 'success');
    await refreshSources();
  } catch {
    addToast(t('tenant.sources.actions.deleteFailed'), 'error');
  } finally { cancelDelete(); }
};
</script>

<style scoped>
.kstats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.kstat {
  padding: 20px 22px; border-radius: var(--radius-xl);
  background: var(--surface-1); border: 1px solid var(--surface-3);
}
.kstat__label {
  font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--surface-muted); margin-bottom: 6px;
}
.kstat__value { font-size: 26px; font-weight: 700; color: var(--surface-heading); font-variant-numeric: tabular-nums; }

.kjobs { display: flex; flex-direction: column; gap: 12px; }
.kjobs__more {
  align-self: center; padding: 6px 14px; border-radius: var(--radius-pill);
  border: 1px solid var(--surface-3); background: none; cursor: pointer;
  font-size: 12px; font-weight: 600; color: var(--surface-muted);
}
.kjobs__more:hover { color: var(--surface-heading); border-color: var(--surface-muted); }
.kempty { font-size: 13px; color: var(--surface-muted); padding: 8px 0; }

.kfiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
.kfile {
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
  border-radius: var(--radius-lg); background: var(--surface-2);
}
.kfile__icon {
  width: 36px; height: 36px; flex-shrink: 0; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  background: rgba(255, 32, 149, 0.12); color: var(--brand-magenta); font-size: 15px;
}
.kfile__info { flex: 1; min-width: 0; }
.kfile__name { font-size: 13px; font-weight: 600; color: var(--surface-heading); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kfile__meta { font-size: 11px; color: var(--surface-muted); margin-top: 2px; }
.kfile__status--completed { color: var(--status-success); }
.kfile__status--error, .kfile__status--unsupported { color: var(--status-warning); }
.kfile__status--processing, .kfile__status--queued { color: var(--brand-cyan); }
.kfile__delete {
  width: 30px; height: 30px; flex-shrink: 0; border: none; background: none; border-radius: var(--radius-md);
  color: var(--surface-muted); cursor: pointer; opacity: 0; transition: opacity var(--t-fast), color var(--t-fast);
}
.kfile:hover .kfile__delete, .kfile__delete:focus-visible { opacity: 1; }
.kfile__delete:hover { color: var(--status-error); }

@media (max-width: 900px) {
  .kstats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .kstat { padding: 14px 16px; }
  .kstat__value { font-size: 20px; }
  .kfile__delete { opacity: 1; }
}
</style>
