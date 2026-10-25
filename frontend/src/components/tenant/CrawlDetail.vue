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
          {{ estimate.to_learn ? $t('knowledge.estimate.body', { n: estimate.to_learn }) : $t('knowledge.estimate.nothing') }}
        </p>
        <p v-if="estimate.index_only" class="meta">
          {{ $t('knowledge.estimate.indexOnly', { n: estimate.index_only, pages: estimate.max_pages }) }}
        </p>

        <!-- What the sorting step set aside: visible, and reversible before learning -->
        <div v-if="estimate.skipped" class="crawl-skipped">
          <div class="crawl-skipped__head">
            <p>
              <strong>{{ $t('knowledge.estimate.skipped', { n: estimate.skipped }) }}</strong>
              <span class="meta"> — {{ skippedSummary }}</span>
            </p>
            <button type="button" class="btn-quiet" :aria-expanded="showSkipped" @click="toggleSkipped">
              {{ showSkipped ? $t('knowledge.estimate.hideList') : $t('knowledge.estimate.showList') }}
            </button>
          </div>
          <div v-if="showSkipped" class="crawl-skipped__list">
            <p v-if="!skipped" class="meta">…</p>
            <section v-for="group in skippedGroups" :key="group.reason" class="crawl-skipped__group">
              <div class="crawl-skipped__group-head">
                <h3>{{ $t(`knowledge.skipReasons.${group.reason}`) }} <span class="meta">({{ group.items.length }})</span></h3>
                <button type="button" class="btn-quiet" :disabled="busy" @click="include(group.items.map((s) => s.id))">{{ $t('knowledge.estimate.includeAll') }}</button>
              </div>
              <ul>
                <li v-for="s in group.items" :key="s.id">
                  <a :href="s.source_location" target="_blank" rel="noopener noreferrer">{{ s.title || pageLabel({ url: s.source_location }) }}</a>
                  <span v-if="s.file_pages" class="meta">{{ $t('knowledge.estimate.pages', { n: s.file_pages }) }}</span>
                  <button type="button" class="crawl-skipped__take" :disabled="busy" @click="include([s.id])">{{ $t('knowledge.estimate.include') }}</button>
                </li>
              </ul>
            </section>
          </div>
        </div>
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
import { ACTIVE_STATUSES, isPreparing, useCrawlActions, useCrawlText } from '@/composables/useCrawl';
import ActivityLog from './sources/ActivityLog.vue';
import CrawlReport from './sources/CrawlReport.vue';
import ConfirmationModal from '../ConfirmationModal.vue';

const props = defineProps({
  tenantId: { type: String, required: true },
  jobId:    { type: [String, Number], required: true },
});
const router = useRouter();
const { t } = useI18n();
const { statusLabel, fmtChf, fmtDateTime, displayUrl, latestPage, pageLabel } = useCrawlText();
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
  const total = estimate.value.to_learn || 0;
  const done = log.value.filter((e) => e.event === 'learned' || e.event === 'learn_failed').length;
  return { percent: total ? Math.min(100, (done / total) * 100) : 0, label: t('knowledge.job.learnProgress', { done, total: total || '…' }) };
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

// ── Sorted out before learning ──────────────────────────────────────
const showSkipped = ref(false);
const skipped = ref(null);
const SKIP_ORDER = ['archive_finance', 'old_minutes', 'outdated', 'older_version', 'internal', 'manual', 'other'];
const skippedSummary = computed(() => Object.entries(estimate.value.skipped_by_reason || {})
  .sort(([a], [b]) => SKIP_ORDER.indexOf(a) - SKIP_ORDER.indexOf(b))
  .map(([reason, n]) => `${t(`knowledge.skipReasons.${reason}`)} ${n}`).join(', '));
const skippedGroups = computed(() => {
  const groups = {};
  for (const s of skipped.value || []) (groups[s.skip_reason || 'other'] ||= []).push(s);
  return SKIP_ORDER.filter((r) => groups[r]).map((reason) => ({ reason, items: groups[reason] }));
});
const loadSkipped = async () => {
  try { skipped.value = (await apiClient.get(`${base.value}/skipped`)).data; }
  catch { skipped.value = []; }
};
const toggleSkipped = () => {
  showSkipped.value = !showSkipped.value;
  if (showSkipped.value && !skipped.value) loadSkipped();
};
const include = async (ids) => {
  busy.value = true;
  try {
    const { data } = await apiClient.post(`${base.value}/selection`, { include: ids });
    job.value = { ...job.value, estimate: data };
    skipped.value = (skipped.value || []).filter((s) => !ids.includes(s.id));
  } catch { /* the toast in actions covers other errors; keep the list as it is */ }
  finally { busy.value = false; }
};

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
.crawl-skipped { border-top: 1px solid var(--surface-3); padding-top: 14px; display: flex; flex-direction: column; gap: 12px; }
.crawl-skipped__head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.crawl-skipped__head p { font-size: 15px; color: var(--surface-heading); max-width: var(--measure); }
.crawl-skipped__list { display: flex; flex-direction: column; gap: 16px; max-height: 480px; overflow-y: auto; padding-right: 4px; }
.crawl-skipped__group-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 6px; }
.crawl-skipped__group-head h3 { font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.crawl-skipped__group ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; }
.crawl-skipped__group li { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; align-items: baseline; gap: 12px; padding: 7px 0; border-top: 1px solid var(--surface-3); font-size: var(--text-sm); }
.crawl-skipped__group li a { color: var(--surface-text); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crawl-skipped__group li a:hover { color: var(--interactive); text-decoration: underline; }
.crawl-skipped__take { border: none; background: none; padding: 0; cursor: pointer; font: inherit; font-size: var(--text-sm); font-weight: 600; color: var(--interactive); }
.crawl-skipped__take:disabled { opacity: 0.5; cursor: not-allowed; }
.crawl-reading { display: flex; align-items: center; gap: 12px; font-size: 15px; color: var(--surface-heading); }
.crawl-reading p { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.crawl-pulse { flex-shrink: 0; width: 10px; height: 10px; border-radius: 50%; background: var(--ai); animation: crawl-pulse 1.2s ease-in-out infinite; }
@keyframes crawl-pulse { 0%, 100% { opacity: 0.35; transform: scale(0.85); } 50% { opacity: 1; transform: scale(1); } }
@media (prefers-reduced-motion: reduce) { .crawl-pulse { animation: none; } }
.crawl-progress__bar { height: 6px; border-radius: var(--radius-pill); background: var(--surface-3); overflow: hidden; }
.crawl-progress__fill { height: 100%; width: 0; background: var(--ai); transition: width var(--t-slow); }

.crawl-section-title { margin-bottom: 8px; }
</style>
