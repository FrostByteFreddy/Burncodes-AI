<template>
  <article class="cjc" :class="`cjc--${job.status.toLowerCase()}`">
    <header class="cjc__head">
      <div class="cjc__icon"><font-awesome-icon :icon="['fas', 'globe']" /></div>
      <div class="cjc__info">
        <a :href="job.start_url" target="_blank" rel="noopener noreferrer" class="cjc__url" :title="$t('knowledge.tree.open')">
          {{ displayUrl }}
          <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="cjc__url-icon" />
        </a>
        <p class="cjc__meta">
          {{ job.trigger === 'scheduled' ? $t('knowledge.job.scheduled', { date: fmtDate(job.created_at) }) : $t('knowledge.job.started', { date: fmtDate(job.created_at) }) }}
          <template v-if="job.single_page_only"> · {{ $t('knowledge.job.singlePage') }}</template>
        </p>
      </div>
      <span class="cjc__pill" :class="`cjc__pill--${job.status.toLowerCase()}`">
        <font-awesome-icon v-if="isActive && job.status !== 'SCANNED'" :icon="['fas', 'spinner']" class="animate-spin" />
        {{ $t(`knowledge.status.${job.status}`) }}
      </span>
      <div class="cjc__actions">
        <button v-if="job.status === 'IN_PROGRESS' || job.status === 'INDEXING'" class="cjc__btn" :disabled="busy" @click="$emit('stop', job)">
          <font-awesome-icon :icon="['fas', 'stop']" /> {{ $t('knowledge.job.stop') }}
        </button>
        <button v-if="!isActive" class="cjc__icon-btn" :title="$t('knowledge.job.delete')" :aria-label="$t('knowledge.job.delete')" @click="$emit('delete', job)">
          <font-awesome-icon :icon="['fas', 'trash-alt']" />
        </button>
      </div>
    </header>

    <!-- Scanning -->
    <div v-if="job.status === 'IN_PROGRESS'" class="cjc__body">
      <div class="cjc__progress">
        <div class="cjc__bar"><div class="cjc__bar-fill" :style="scanBarStyle"></div></div>
        <span class="cjc__progress-label">{{ $t('knowledge.job.scanProgress', { done: scanDone, total: Math.max(scanTotal, scanDone) || '…' }) }}</span>
      </div>
      <ActivityLog :entries="log" />
    </div>

    <!-- Scan finished: estimate + confirmation -->
    <div v-else-if="job.status === 'SCANNED'" class="cjc__body">
      <div class="cjc__estimate">
        <p class="cjc__estimate-title">{{ $t('knowledge.estimate.title') }}</p>
        <div class="cjc__chips">
          <span v-for="chip in outcomeChips" :key="chip.key" class="cjc__chip" :class="`cjc__chip--${chip.key}`">
            <strong>{{ chip.n }}</strong> {{ $t(`knowledge.estimate.${chip.key}`) }}
          </span>
        </div>
        <p class="cjc__estimate-body">
          {{ estimate.to_learn ? $t('knowledge.estimate.body', { n: estimate.to_learn }) : $t('knowledge.estimate.nothing') }}
        </p>
        <div class="cjc__estimate-actions">
          <button class="cjc__cta" :disabled="busy || !estimate.to_learn" @click="confirm">
            <font-awesome-icon v-if="busy" :icon="['fas', 'spinner']" class="animate-spin" />
            <font-awesome-icon v-else :icon="['fas', 'wand-magic-sparkles']" />
            {{ $t('knowledge.estimate.learn', { cost: fmtChf(estimate.cost_chf) }) }}
          </button>
          <button class="cjc__btn" :disabled="busy" @click="$emit('stop', job)">{{ $t('knowledge.job.discard') }}</button>
        </div>
      </div>
    </div>

    <!-- Learning -->
    <div v-else-if="job.status === 'INDEXING'" class="cjc__body">
      <div class="cjc__progress">
        <div class="cjc__bar"><div class="cjc__bar-fill" :style="{ width: learnPercent + '%' }"></div></div>
        <span class="cjc__progress-label">{{ $t('knowledge.job.learnProgress', { done: learnDone, total: estimate.to_learn || '…' }) }}</span>
      </div>
      <ActivityLog :entries="log" />
    </div>

    <!-- Completed -->
    <div v-else-if="job.status === 'COMPLETED' && job.report" class="cjc__body">
      <button class="cjc__toggle" :aria-expanded="showReport" @click="toggleReport">
        <font-awesome-icon :icon="['fas', showReport ? 'chevron-down' : 'chevron-right']" />
        {{ showReport ? $t('knowledge.job.hideReport') : $t('knowledge.job.report') }}
        <span class="cjc__toggle-meta">
          {{ $t('knowledge.report.learned') }} {{ job.report.counts?.learned || 0 }}
          · {{ $t('knowledge.report.unchanged') }} {{ job.report.counts?.unchanged || 0 }}
          · CHF {{ fmtChf(job.report.cost_chf) }}
        </span>
        <span v-if="job.report.attention?.length" class="cjc__review-badge">
          <font-awesome-icon :icon="['fas', 'triangle-exclamation']" /> {{ job.report.attention.length }}
        </span>
      </button>
      <CrawlReport v-if="showReport" :report="job.report" />
    </div>
  </article>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useToast } from '../../../composables/useToast';
import ActivityLog from './ActivityLog.vue';
import CrawlReport from './CrawlReport.vue';

const props = defineProps({
  job:      { type: Object, required: true },
  tenantId: { type: String, required: true },
  log:      { type: Array, default: () => [] },
  // newest job opens its report by default
  expanded: { type: Boolean, default: false },
});
const emit = defineEmits(['stop', 'delete', 'confirmed']);
const { t, locale } = useI18n();
const { addToast } = useToast();

const busy = ref(false);
const showReport = ref(props.expanded);
const scanTotal = ref(0);

const ACTIVE = ['IN_PROGRESS', 'SCANNED', 'INDEXING'];
const isActive = computed(() => ACTIVE.includes(props.job.status));
const estimate = computed(() => props.job.estimate || {});

const displayUrl = computed(() => props.job.start_url.replace(/^https?:\/\//, ''));

const OUTCOMES = ['new', 'changed', 'unchanged', 'removed', 'error', 'empty', 'refused', 'unsupported'];
const outcomeChips = computed(() => {
  const o = { ...(estimate.value.outcomes || {}), removed: estimate.value.removed || 0 };
  return OUTCOMES.filter((k) => o[k]).map((key) => ({ key, n: o[key] }));
});

// Progress straight from the live activity log
const scanDone = computed(() => props.log.filter((e) => e.event === 'scanned').length);
const learnDone = computed(() => props.log.filter((e) => e.event === 'learned' || e.event === 'learn_failed').length);
const learnPercent = computed(() => {
  const total = estimate.value.to_learn || 0;
  return total ? Math.min(100, (learnDone.value / total) * 100) : 0;
});
const scanBarStyle = computed(() => {
  const total = Math.max(scanTotal.value, scanDone.value);
  return total ? { width: `${Math.min(100, (scanDone.value / total) * 100)}%` } : {};
});

// The total grows while links are discovered; refresh it as the log moves
const fetchScanTotal = async () => {
  if (props.job.status !== 'IN_PROGRESS') return;
  try {
    const r = await apiClient.get(`/tenants/${props.tenantId}/crawling_jobs/${props.job.id}/progress`);
    scanTotal.value = r.data.total || 0;
  } catch { /* progress is cosmetic */ }
};
onMounted(fetchScanTotal);
let totalTimer = null;
watch(() => props.log.length, () => {
  clearTimeout(totalTimer);
  totalTimer = setTimeout(fetchScanTotal, 800);
});

const toggleReport = () => { showReport.value = !showReport.value; };

const confirm = async () => {
  busy.value = true;
  try {
    await apiClient.post(`/tenants/${props.tenantId}/crawling_jobs/${props.job.id}/confirm`);
    addToast(t('knowledge.estimate.started'), 'success');
    emit('confirmed', props.job.id);
  } catch (e) {
    if (e.response?.status === 402) {
      const d = e.response.data || {};
      addToast(t('knowledge.estimate.balanceLow', { balance: fmtChf(d.balance_chf), cost: fmtChf(d.estimate_chf) }), 'error');
    } else {
      addToast(e.response?.data?.error || 'Error', 'error');
    }
  } finally {
    busy.value = false;
  }
};

const fmtChf = (v) => Number(v || 0).toFixed(2);
const fmtDate = (iso) => new Date(iso).toLocaleString(locale.value, { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
</script>

<style scoped>
.cjc {
  display: flex; flex-direction: column; gap: 14px;
  padding: 16px 18px; border-radius: var(--radius-lg);
  background: var(--surface-2); border: 1px solid transparent;
  transition: border-color var(--t-fast);
}
.cjc--scanned { border-color: rgba(80, 211, 252, 0.3); }
.cjc--in_progress, .cjc--indexing { border-color: rgba(10, 31, 171, 0.45); }

.cjc__head { display: flex; align-items: center; gap: 14px; min-width: 0; }
.cjc__icon {
  width: 40px; height: 40px; flex-shrink: 0; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  background: rgba(10, 31, 171, 0.15); color: var(--brand-cyan); font-size: 15px;
}
.cjc__info { flex: 1; min-width: 0; }
.cjc__url {
  display: block; font-size: 14px; font-weight: 600; color: var(--surface-heading);
  text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cjc__url:hover { color: var(--brand-cyan); }
.cjc__url-icon { font-size: 9px; margin-left: 4px; opacity: 0.5; }
.cjc__meta { font-size: 12px; color: var(--surface-muted); margin-top: 2px; }

.cjc__pill {
  flex-shrink: 0; display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: var(--radius-pill);
  background: var(--surface-3); color: var(--surface-text);
}
.cjc__pill--in_progress, .cjc__pill--indexing { background: rgba(10, 31, 171, 0.25); color: var(--brand-cyan); }
.cjc__pill--scanned { background: var(--gradient-brand); color: #fff; }
.cjc__pill--completed { background: rgba(0, 201, 167, 0.12); color: var(--status-success); }
.cjc__pill--failed { background: rgba(245, 158, 11, 0.12); color: var(--status-warning); }

.cjc__actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.cjc__btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border-radius: var(--radius-pill);
  border: 1px solid var(--surface-3); background: none;
  font-size: 12px; font-weight: 600; color: var(--surface-text); cursor: pointer;
  transition: border-color var(--t-fast), color var(--t-fast);
}
.cjc__btn:hover:not(:disabled) { border-color: var(--status-warning); color: var(--status-warning); }
.cjc__btn:disabled { opacity: 0.45; cursor: not-allowed; }
.cjc__icon-btn {
  width: 32px; height: 32px; border-radius: var(--radius-md); border: none; background: none;
  display: flex; align-items: center; justify-content: center;
  color: var(--surface-muted); cursor: pointer; transition: color var(--t-fast), background var(--t-fast);
}
.cjc__icon-btn:hover { color: var(--status-error); background: rgba(255, 68, 68, 0.08); }

.cjc__body { display: flex; flex-direction: column; gap: 14px; padding-left: 54px; max-width: 980px; }

.cjc__progress { display: flex; flex-direction: column; gap: 6px; }
.cjc__bar { height: 6px; border-radius: var(--radius-pill); background: var(--surface-3); overflow: hidden; }
.cjc__bar-fill { height: 100%; width: 0; background: var(--gradient-brand); transition: width var(--t-slow); }
.cjc__progress-label { font-size: 12px; color: var(--surface-muted); font-variant-numeric: tabular-nums; }

.cjc__estimate {
  display: flex; flex-direction: column; gap: 10px;
  padding: 16px; border-radius: var(--radius-md);
  background: var(--gradient-brand-soft); border: 1px solid rgba(80, 211, 252, 0.2);
}
.cjc__estimate-title { font-size: 14px; font-weight: 700; color: var(--surface-heading); }
.cjc__estimate-body { font-size: 13px; color: var(--surface-text); line-height: 1.55; }
.cjc__chips { display: flex; flex-wrap: wrap; gap: 6px; }
.cjc__chip {
  font-size: 12px; padding: 3px 10px; border-radius: var(--radius-pill);
  background: var(--surface-1); color: var(--surface-muted);
}
.cjc__chip strong { color: var(--surface-heading); }
.cjc__chip--new strong, .cjc__chip--changed strong { color: var(--brand-cyan); }
.cjc__chip--error strong, .cjc__chip--removed strong, .cjc__chip--refused strong { color: var(--status-warning); }
.cjc__estimate-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 2px; }
.cjc__cta {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 18px; border: none; border-radius: var(--radius-pill);
  background: var(--gradient-brand); color: #fff; font-size: 13px; font-weight: 700; cursor: pointer;
  transition: opacity var(--t-fast);
}
.cjc__cta:hover:not(:disabled) { opacity: 0.9; }
.cjc__cta:disabled { opacity: 0.45; cursor: not-allowed; }

.cjc__toggle {
  display: flex; align-items: center; flex-wrap: wrap; gap: 8px; align-self: flex-start;
  border: none; background: none; padding: 0; cursor: pointer; text-align: left;
  font-size: 13px; font-weight: 600; color: var(--surface-heading);
}
.cjc__toggle-meta { font-weight: 400; font-size: 12px; color: var(--surface-muted); }
.cjc__review-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: var(--radius-pill);
  background: rgba(245, 158, 11, 0.12); color: var(--status-warning);
}

@media (max-width: 640px) {
  .cjc__head { flex-wrap: wrap; }
  .cjc__info { flex-basis: calc(100% - 54px); }
  .cjc__body { padding-left: 0; }
}
</style>
