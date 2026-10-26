<template>
  <div class="crawl-page">
    <router-link :to="{ name: 'TenantSources', params: { tenantId } }" class="crawl-back">
      <font-awesome-icon :icon="['fas', 'chevron-left']" />
      {{ $t('knowledge.job.back') }}
    </router-link>

    <template v-if="!job && loading">
      <div class="ghost-stack" aria-busy="true">
        <span class="ghost ghost--pill"></span>
        <span class="ghost ghost--title" style="width: 45%; height: 26px"></span>
        <span class="ghost ghost--line" style="width: 30%"></span>
      </div>
      <section class="panel ghost-stack">
        <span class="ghost ghost--title" style="width: 160px"></span>
        <span v-for="n in 3" :key="n" class="ghost ghost--line" :style="{ width: `${85 - n * 15}%` }"></span>
      </section>
      <section class="panel">
        <div v-for="n in 6" :key="n" class="ghost-row"><span class="ghost ghost--dot" style="width: 10px; height: 10px"></span><span class="ghost ghost--line" :style="{ width: `${60 - (n % 3) * 12}%` }"></span></div>
      </section>
    </template>
    <p v-else-if="!job" class="meta">{{ $t('knowledge.job.actionFailed') }}</p>

    <template v-else>
      <div class="page-head">
        <div class="crawl-head">
          <span class="crawl-status" :class="`crawl-status--${job.status.toLowerCase()}`">
            <font-awesome-icon v-if="job.status === 'IN_PROGRESS' || job.status === 'INDEXING' || isPreparing(job)" :icon="['fas', 'spinner']" class="animate-spin" />
            {{ statusLabel(job) }}
          </span>
          <h1 class="page-title crawl-title">{{ displayUrl(job.start_url) }}</h1>
          <p class="page-lede">
            {{ job.trigger === 'scheduled' ? $t('knowledge.job.scheduled', { date: fmtDateTime(job.created_at) }) : $t('knowledge.job.started', { date: fmtDateTime(job.created_at) }) }}<template v-if="job.single_page_only">. {{ $t('knowledge.job.singlePage') }}.</template>
          </p>
        </div>
        <div class="page-actions">
          <a :href="job.start_url" target="_blank" rel="noopener noreferrer" class="btn-quiet">
            <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" />
            {{ $t('knowledge.job.openSite') }}
          </a>
          <button v-if="job.status === 'IN_PROGRESS' || job.status === 'INDEXING'" class="btn-quiet" :disabled="busy" @click="onStop">
            <font-awesome-icon :icon="['fas', 'stop']" /> {{ $t('knowledge.job.stop') }}
          </button>
          <button v-if="!isActive" class="btn-quiet btn-quiet--danger" @click="askDelete = true">
            <font-awesome-icon :icon="['fas', 'trash-alt']" /> {{ $t('knowledge.job.delete') }}
          </button>
        </div>
      </div>

      <!-- Scan finished: what learning will do and cost -->
      <section v-if="isPreparing(job)" class="panel crawl-reading">
        <span class="crawl-pulse" aria-hidden="true"></span>
        <p>{{ $t('knowledge.estimate.preparing') }}</p>
      </section>
      <section v-else-if="job.status === 'SCANNED'" class="panel crawl-estimate">
        <h2 class="panel-title">{{ $t('knowledge.estimate.title') }}</h2>
        <ul class="crawl-outcomes">
          <li v-for="o in outcomes" :key="o.key"><strong>{{ o.n }}</strong> {{ $t(`knowledge.estimate.${o.key}`) }}</li>
        </ul>
        <p class="crawl-estimate__body">
          {{ estimate.to_learn ? $t('knowledge.estimate.body', { n: estimate.to_learn }) : $t(estimate.skipped ? 'knowledge.estimate.noneSelected' : 'knowledge.estimate.nothing') }}
        </p>
        <p v-if="estimate.index_only" class="meta">
          {{ $t('knowledge.estimate.indexOnly', { n: estimate.index_only, pages: estimate.max_pages }) }}
        </p>

        <!-- Gemini's savings suggestions, what was sorted out, and the folder tree -->
        <CrawlSelection :key="job.id" :base="base" :host="displayUrl(job.start_url)" @estimate="onEstimate" />
        <div class="page-actions">
          <button class="btn-action" :disabled="busy || !estimate.to_learn" @click="onConfirm">
            <font-awesome-icon v-if="busy" :icon="['fas', 'spinner']" class="animate-spin" />
            {{ $t('knowledge.estimate.learn', { cost: fmtChf(estimate.cost_chf) }) }}
          </button>
          <button class="btn-quiet" :disabled="busy" @click="onStop">{{ $t('knowledge.job.discard') }}</button>
        </div>
      </section>

      <!-- Scanning: what's being read (no total, it isn't known yet) -->
      <section v-if="job.status === 'IN_PROGRESS'" class="panel crawl-reading">
        <span class="crawl-pulse" aria-hidden="true"></span>
        <p>{{ latestPage(log) ? $t('knowledge.job.reading', { page: latestPage(log) }) : $t('knowledge.job.starting') }}</p>
      </section>
      <!-- Learning: a real bar, the number of pages is known -->
      <section v-if="job.status === 'INDEXING'" class="panel crawl-progress">
        <div class="crawl-progress__bar"><div class="crawl-progress__fill" :style="{ width: progress.percent + '%' }"></div></div>
        <p class="meta">{{ progress.label }}</p>
      </section>

      <!-- Done: the report -->
      <section v-if="job.status === 'COMPLETED' && job.report" class="panel">
        <CrawlReport :report="job.report" />
      </section>

      <!-- Activity: live while running, history afterwards -->
      <section class="panel">
        <h2 class="panel-title crawl-section-title">{{ $t('knowledge.job.activity') }}</h2>
        <ActivityLog :entries="log" :max-height="isActive ? '560px' : '360px'" />
      </section>
    </template>

    <ConfirmationModal
      :show="askDelete"
      :title="$t('knowledge.deleteJob.title')"
      :message="$t('knowledge.deleteJob.message', { url: escapeHtml(job?.start_url) })"
      :confirmButtonText="$t('tenant.sources.deleteModal.confirm')"
      @confirm="onDelete"
      @cancel="askDelete = false"
    />
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { supabase } from '@/supabase';
import { escapeHtml } from '@/utils/escapeHtml';
import { ACTIVE_STATUSES, isPreparing, learnProgress, useCrawlActions, useCrawlText } from '@/composables/useCrawl';
import ActivityLog from './sources/ActivityLog.vue';
import CrawlReport from './sources/CrawlReport.vue';
import CrawlSelection from './sources/CrawlSelection.vue';
import ConfirmationModal from '../ConfirmationModal.vue';

const props = defineProps({
  tenantId: { type: String, required: true },
  jobId:    { type: [String, Number], required: true },
});
const router = useRouter();
const { t } = useI18n();
const { statusLabel, fmtChf, fmtDateTime, displayUrl, latestPage } = useCrawlText();
const actions = useCrawlActions(() => props.tenantId);

const job = ref(null);
const log = ref([]);
const loading = ref(false);
const busy = ref(false);
const askDelete = ref(false);

const isActive = computed(() => job.value && ACTIVE_STATUSES.includes(job.value.status));
const estimate = computed(() => job.value?.estimate || {});

const OUTCOMES = ['new', 'changed', 'unchanged', 'removed', 'error', 'empty', 'refused', 'unsupported'];
const outcomes = computed(() => {
  const o = { ...(estimate.value.outcomes || {}), removed: estimate.value.removed || 0 };
  return OUTCOMES.filter((k) => o[k]).map((key) => ({ key, n: o[key] }));
});

const progress = computed(() => {
  const { done, total, percent } = learnProgress(job.value, log.value);
  return { percent, label: t('knowledge.job.learnProgress', { done, total: total || '…' }) };
});

const base = computed(() => `/tenants/${props.tenantId}/crawling_jobs/${props.jobId}`);
const fetchJob = async () => {
  try {
    job.value = (await apiClient.get(base.value)).data;
  } catch { job.value = null; }
};
const fetchLog = async () => {
  try {
    log.value = (await apiClient.get(`${base.value}/log`, { params: { limit: 500 } })).data;
  } catch { /* log is supplementary */ }
};

// Realtime: this job's activity and status; polling while it runs as a safety net
let channel = null;
let poll = null;
const subscribe = () => {
  if (channel) supabase.removeChannel(channel);
  channel = supabase
    .channel(`crawl-${props.jobId}`)
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'crawl_job_log', filter: `job_id=eq.${props.jobId}` }, (payload) => {
      if (!log.value.some((e) => e.id === payload.new.id)) log.value = [...log.value, payload.new];
    })
    .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'crawling_jobs', filter: `id=eq.${props.jobId}` }, fetchJob)
    .subscribe();
};

watch(() => [props.tenantId, props.jobId], async () => {
  loading.value = true;
  await Promise.all([fetchJob(), fetchLog()]);
  loading.value = false;
  subscribe();
}, { immediate: true });

watch(isActive, (active) => {
  clearInterval(poll);
  if (active) poll = setInterval(() => { fetchJob(); fetchLog(); }, 5000);
}, { immediate: true });

onUnmounted(() => {
  if (channel) supabase.removeChannel(channel);
  clearInterval(poll);
});

// ── The selection changed: the estimate comes back recomputed ──
const onEstimate = (estimate) => { job.value = { ...job.value, estimate }; };

const onConfirm = async () => {
  busy.value = true;
  if (await actions.confirm(job.value)) await fetchJob();
  busy.value = false;
};
const onStop = async () => {
  busy.value = true;
  if (await actions.stop(job.value)) await fetchJob();
  busy.value = false;
};
const onDelete = async () => {
  askDelete.value = false;
  if (await actions.remove(job.value)) router.push({ name: 'TenantSources', params: { tenantId: props.tenantId } });
};
</script>

<style scoped>
.crawl-page { display: flex; flex-direction: column; gap: 20px; }
.crawl-back {
  align-self: flex-start;
  display: inline-flex; align-items: center; gap: 8px;
  font-size: var(--text-sm); font-weight: 600; color: var(--surface-muted); text-decoration: none;
}
.crawl-back:hover { color: var(--interactive); }

.crawl-head { min-width: 0; }
.crawl-title { overflow-wrap: anywhere; margin-top: 10px; }
.crawl-status {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px; border-radius: var(--radius-pill);
  font-size: var(--text-xs); font-weight: 700;
  background: var(--surface-2); color: var(--surface-text);
}
.crawl-status--in_progress, .crawl-status--indexing { background: var(--ai-soft); color: var(--ai); }
.crawl-status--scanned { background: var(--interactive-soft); color: var(--interactive); }
.crawl-status--completed { background: var(--status-success-soft); color: var(--status-success); }
.crawl-status--failed { background: var(--status-warning-soft); color: var(--status-warning); }

.page-actions .btn-quiet { text-decoration: none; }
.btn-quiet--danger:hover:not(:disabled) { border-color: var(--status-error); color: var(--status-error); }

.crawl-estimate { display: flex; flex-direction: column; gap: 14px; border-color: var(--interactive-strong); }
.crawl-outcomes { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 15px; color: var(--surface-muted); }
.crawl-outcomes strong { color: var(--surface-heading); font-size: var(--text-lg); margin-right: 2px; }
.crawl-estimate__body { font-size: 15px; color: var(--surface-text); max-width: var(--measure); }

.crawl-progress { display: flex; flex-direction: column; gap: 8px; }
.crawl-reading { display: flex; align-items: center; gap: 12px; font-size: 15px; color: var(--surface-heading); }
.crawl-reading p { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crawl-pulse { flex-shrink: 0; width: 10px; height: 10px; border-radius: 50%; background: var(--ai); animation: crawl-pulse 1.2s ease-in-out infinite; }
@keyframes crawl-pulse { 0%, 100% { opacity: 0.35; transform: scale(0.85); } 50% { opacity: 1; transform: scale(1); } }
@media (prefers-reduced-motion: reduce) { .crawl-pulse { animation: none; } }
.crawl-progress__bar { height: 6px; border-radius: var(--radius-pill); background: var(--surface-3); overflow: hidden; }
.crawl-progress__fill { height: 100%; width: 0; background: var(--ai); transition: width var(--t-slow); }

.crawl-section-title { margin-bottom: 8px; }
</style>
