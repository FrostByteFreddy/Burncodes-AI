<template>
  <div class="sources-page">

    <div class="page-head">
      <div>
        <h1 class="page-title">{{ $t('pages.knowledgeTitle') }}</h1>
        <p class="page-lede">{{ $t('pages.knowledge') }}</p>
        <p class="ksummary">{{ summary }}</p>
      </div>
      <div class="page-actions">
        <BcButton variant="primary"  @click="wizardOpen = true">
          <font-awesome-icon :icon="['fas', 'plus']" />
          {{ $t('tenant.sources.wizard.addKnowledge') }}
        </BcButton>
      </div>
    </div>

    <KnowledgeOverview v-if="tenantId" :tenant-id="tenantId" :refresh-key="overviewKey" />

    <!-- ── Crawls ───────────────────────────────────────────── -->
    <section class="knowledge-panel">
      <div class="knowledge-panel__header">
        <div class="knowledge-panel__header-left">
          <div>
            <h2 class="knowledge-panel__title">{{ $t('knowledge.crawls.title') }}</h2>
            <p class="knowledge-panel__sub">{{ $t('knowledge.crawls.sub') }}</p>
          </div>
        </div>
      </div>
      <p v-if="crawlingJobs.length" class="krecrawl__hint">
        {{ tenantsStore.currentTenant?.auto_recrawl ? $t('knowledge.recrawl.onHint', { n: tenantsStore.currentTenant.recrawl_interval_days || 7 }) : $t('knowledge.recrawl.offHint') }}
        <router-link :to="{ name: 'TenantSettings', params: { tenantId } }">{{ $t('knowledge.recrawl.change') }}</router-link>
      </p>

      <div v-if="!jobsLoaded" aria-busy="true">
        <div v-for="n in 2" :key="n" class="ghost-row">
          <span class="ghost ghost--pill"></span>
          <div class="ghost-stack" style="flex: 1"><span class="ghost ghost--line" style="width: 55%"></span><span class="ghost ghost--line" style="width: 30%; height: 10px"></span></div>
          <span class="ghost ghost--btn" style="width: 76px"></span>
        </div>
      </div>
      <template v-else-if="shownJobs.length">
        <ol class="kjobs">
          <CrawlJobRow
            v-for="job in shownJobs"
            :key="job.id"
            :job="job"
            :tenant-id="tenantId"
            :log="logsByJob[job.id] || []"
            @changed="onJobChanged"
          />
        </ol>
        <button v-if="crawlingJobs.length > JOBS_SHOWN" class="kjobs__more" @click="showAllJobs = !showAllJobs">
          {{ showAllJobs ? $t('knowledge.crawls.showLess') : $t('knowledge.crawls.showAll', { n: crawlingJobs.length }) }}
        </button>
      </template>
      <p v-else class="kempty">{{ $t('knowledge.crawls.empty') }}</p>
    </section>

    <!-- ── Uploaded files ───────────────────────────────────── -->
    <section class="knowledge-panel">
      <div class="knowledge-panel__header">
        <div class="knowledge-panel__header-left">
          <div>
            <h2 class="knowledge-panel__title">{{ $t('knowledge.files.title') }}</h2>
            <p class="knowledge-panel__sub">{{ $t('knowledge.files.sub') }}</p>
          </div>
        </div>
        <BcButton variant="secondary" @click="wizardOpen = true">
          <font-awesome-icon :icon="['fas', 'arrow-up-from-bracket']" />
          {{ $t('knowledge.files.upload') }}
        </BcButton>
      </div>

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
          <div>
            <h2 class="knowledge-panel__title">{{ $t('knowledge.rules.title') }}</h2>
            <p class="knowledge-panel__sub">{{ $t('knowledge.rules.sub') }}</p>
          </div>
        </div>
        <BcButton variant="secondary" @click="rulesTabRef?.openModal()">
          <font-awesome-icon :icon="['fas', 'plus']" />
          {{ $t('knowledge.rules.add') }}
        </BcButton>
      </div>
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
      :loading="deleting"
      @confirm="handleDelete"
      @cancel="cancelDelete"
    />

  </div>
</template>

<script setup>
import { BcButton } from '@/components/ui';
import { computed, onUnmounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../../stores/tenants';
import { useToast } from '../../composables/useToast';
import apiClient from '@/utils/api';
import { supabase } from '@/supabase';
import { escapeHtml } from '@/utils/escapeHtml';
import { formatNumber } from '@/utils/format';
import AddKnowledgeWizard from './sources/AddKnowledgeWizard.vue';
import CrawlJobRow from './sources/CrawlJobRow.vue';
import KnowledgeOverview from './sources/KnowledgeOverview.vue';
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
const jobsLoaded            = ref(false);
const logsByJob             = ref({});
const showAllJobs           = ref(false);
const sourceToDelete        = ref(null);
const showConfirmationModal = ref(false);
const deleting = ref(false);
const rulesTabRef           = ref(null);

const tenantId = computed(() => tenantsStore.currentTenant?.id || '');
const allSources = computed(() => tenantsStore.currentTenant?.tenant_sources || []);
const fileSources = computed(() => allSources.value.filter((s) => s.source_type === 'FILE'));
const shownJobs = computed(() => (showAllJobs.value ? crawlingJobs.value : crawlingJobs.value.slice(0, JOBS_SHOWN)));
const hasActiveJob = computed(() => crawlingJobs.value.some((j) => ACTIVE.includes(j.status)));

// ── One-sentence summary (each URL once — older crawls stored duplicates) ──
const summary = computed(() => {
  const unique = new Map();
  for (const src of allSources.value) unique.set(`${src.source_type}:${src.source_location}`, src);
  const learned = [...unique.values()].filter((src) => src.status === 'COMPLETED');
  if (!learned.length) return t('knowledge.overview.summaryNever');
  const lastCrawl = crawlingJobs.value[0]?.created_at;
  return t('knowledge.overview.summary', {
    sources: formatNumber(learned.length),
    chunks: formatNumber(learned.reduce((n, src) => n + (src.indexed_chunks || 0), 0)),
    date: lastCrawl ? new Date(lastCrawl).toLocaleDateString(locale.value, { day: 'numeric', month: 'long' }) : '—',
  });
});

// Bumped when a crawl finishes so the date strip reloads
const overviewKey = ref(0);

// ── Data ───────────────────────────────────────────────────────────────
const fetchCrawlingJobs = async () => {
  if (!tenantId.value) return;
  try {
    const r = await apiClient.get(`/tenants/${tenantId.value}/crawling_jobs`);
    crawlingJobs.value = r.data;
  } catch { addToast(t('tenant.sources.actions.fetchFailed'), 'error'); }
  finally { jobsLoaded.value = true; }
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
      if (after === 'COMPLETED') overviewKey.value += 1;
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
  jobsLoaded.value = false;
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
  deleting.value = true;
  try {
    await apiClient.delete(`/tenants/${tenantId.value}/sources/${id}`);
    addToast(t('tenant.sources.actions.deleteSuccess'), 'success');
    await refreshSources();
  } catch (e) {
    addToast(t(e.response?.data?.code === 'gemini_failed' ? 'common.geminiFailed' : 'tenant.sources.actions.deleteFailed'), 'error');
  } finally { deleting.value = false; cancelDelete(); }
};
</script>

<style scoped>
.ksummary { margin-top: 10px; font-size: var(--text-sm); color: var(--surface-text); }

.kjobs { list-style: none; padding: 0; margin: 0; }
.krecrawl__hint { margin: -6px 0 12px; font-size: var(--text-sm); color: var(--surface-muted); max-width: var(--measure); }
.krecrawl__hint a { color: var(--interactive); font-weight: 600; }
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

@media (max-width: 640px) {
  .kfile__delete { opacity: 1; }
}
</style>
