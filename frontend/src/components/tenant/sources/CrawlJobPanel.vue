<template>
  <!-- Scan finished: estimate + confirm -->
  <div v-if="job.status === 'SCANNED'" class="cjp cjp--confirm">
    <p class="cjp__title">Scan complete — ready to learn</p>
    <div class="cjp__chips">
      <span v-for="chip in outcomeChips" :key="chip.key" class="cjp__chip" :class="`cjp__chip--${chip.key}`">
        {{ chip.n }} {{ chip.label }}
      </span>
    </div>
    <p v-if="estimate.to_learn > 0" class="cjp__text">
      Gemini will read <strong>{{ estimate.to_learn }}</strong> new or changed
      {{ estimate.to_learn === 1 ? 'source' : 'sources' }}
      <template v-if="estimate.files">({{ estimate.pages }} pages, {{ estimate.files }} files)</template>,
      split them into sections, note important facts and dates, and index them.
      Unchanged pages are skipped for free.
    </p>
    <p v-else class="cjp__text">Nothing changed since the last crawl — nothing to learn.</p>
    <div class="cjp__actions">
      <button class="cjp__btn cjp__btn--primary" :disabled="busy || estimate.to_learn === 0" @click="confirm">
        <font-awesome-icon v-if="busy" :icon="['fas', 'spinner']" class="animate-spin" />
        Learn now · approx. CHF {{ fmtChf(estimate.cost_chf) }}
      </button>
      <button class="cjp__btn" :disabled="busy" @click="$emit('cancel', job)">Discard</button>
    </div>
  </div>

  <!-- Learning in progress -->
  <div v-else-if="job.status === 'INDEXING'" class="cjp">
    <div class="cjp__bar"><div class="cjp__bar-fill" :style="{ width: learnPercent + '%' }"></div></div>
    <p class="cjp__meta">Learning · {{ learnedCount }} / {{ estimate.to_learn || '?' }} sources</p>
  </div>

  <!-- Report -->
  <div v-else-if="job.status === 'COMPLETED' && report" class="cjp">
    <button class="cjp__toggle" @click="open = !open">
      <font-awesome-icon :icon="['fas', open ? 'chevron-down' : 'chevron-right']" />
      Crawl report
      <span class="cjp__toggle-meta">
        {{ report.counts?.learned || 0 }} learned · {{ report.counts?.unchanged || 0 }} unchanged
        <template v-if="report.counts?.removed"> · {{ report.counts.removed }} removed</template>
        · CHF {{ fmtChf(report.cost_chf) }}
        <span v-if="attention.length" class="cjp__warn-count">· {{ attention.length }} to review</span>
      </span>
    </button>

    <div v-if="open" class="cjp__report">
      <section v-if="report.highlights?.length">
        <h4 class="cjp__h">Most important content</h4>
        <ul class="cjp__list">
          <li v-for="h in report.highlights" :key="h.source_id">
            <span class="cjp__badge" :class="importanceClass(h.importance)">{{ h.importance }}</span>
            <a :href="h.url" target="_blank" rel="noopener noreferrer" class="cjp__link">{{ h.title }}</a>
            <p class="cjp__sub">{{ h.reason }}</p>
          </li>
        </ul>
      </section>

      <section v-if="report.schedules?.length">
        <h4 class="cjp__h">Dates found and verified</h4>
        <ul class="cjp__list">
          <li v-for="s in report.schedules" :key="`${s.source_id}-${s.series}-${s.zone}`">
            <strong>{{ s.series }}<template v-if="s.zone"> · {{ s.zone }}</template></strong>
            — {{ s.count }} {{ s.count === 1 ? 'date' : 'dates' }}, {{ fmtDay(s.first) }}<template v-if="s.count > 1"> – {{ fmtDay(s.last) }}</template>
            <span v-if="s.expired" class="cjp__expired">expired</span>
            <p class="cjp__sub">{{ s.title }}</p>
          </li>
        </ul>
      </section>

      <section v-if="attention.length">
        <h4 class="cjp__h">Needs your attention</h4>
        <ul class="cjp__list">
          <li v-for="(a, i) in attention" :key="i">
            <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="cjp__warn-icon" />
            {{ a.message }}
            <p class="cjp__sub"><a :href="a.url" target="_blank" rel="noopener noreferrer" class="cjp__link">{{ a.title }}</a></p>
          </li>
        </ul>
      </section>

      <p v-if="errorSummary" class="cjp__sub">Not reachable: {{ errorSummary }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import apiClient from '@/utils/api';
import { useToast } from '../../../composables/useToast';

const props = defineProps({
  job:      { type: Object, required: true },
  tenantId: { type: String, required: true },
});
const emit = defineEmits(['confirmed', 'cancel']);
const { addToast } = useToast();

const busy = ref(false);
const open = ref(false);

const estimate  = computed(() => props.job.estimate || {});
const report    = computed(() => props.job.report || null);
const attention = computed(() => report.value?.attention || []);

const OUTCOMES = [
  ['new', 'new'], ['changed', 'changed'], ['unchanged', 'unchanged'],
  ['removed', 'removed'], ['error', 'errors'], ['empty', 'empty'],
];
const outcomeChips = computed(() => {
  const o = { ...(estimate.value.outcomes || {}), removed: estimate.value.removed || 0 };
  return OUTCOMES.filter(([k]) => o[k]).map(([key, label]) => ({ key, label, n: o[key] }));
});

const learnedCount = computed(() =>
  (props.job.sources || []).filter(s => s.learned_job_id === props.job.id).length
);
const learnPercent = computed(() => {
  const total = estimate.value.to_learn || 0;
  return total ? Math.min(100, (learnedCount.value / total) * 100) : 0;
});

const errorSummary = computed(() =>
  Object.entries(report.value?.errors || {}).map(([code, n]) => `${n}× ${code}`).join(', ')
);

const importanceClass = (n) => (n >= 85 ? 'cjp__badge--high' : n >= 70 ? 'cjp__badge--mid' : '');
const fmtChf = (v) => Number(v || 0).toFixed(2);
const fmtDay = (iso) => (iso ? new Date(iso + 'T00:00:00').toLocaleDateString([], { day: '2-digit', month: '2-digit', year: 'numeric' }) : '');

const confirm = async () => {
  busy.value = true;
  try {
    await apiClient.post(`/tenants/${props.tenantId}/crawling_jobs/${props.job.id}/confirm`);
    addToast('Learning started — you’ll get a report when it’s done.', 'success');
    emit('confirmed', props.job.id);
  } catch (e) {
    if (e.response?.status === 402) {
      const d = e.response.data || {};
      addToast(`Balance too low: CHF ${fmtChf(d.balance_chf)} available, about CHF ${fmtChf(d.estimate_chf)} needed.`, 'error');
    } else {
      addToast(e.response?.data?.error || 'Could not start learning.', 'error');
    }
  } finally {
    busy.value = false;
  }
};
</script>

<style scoped>
.cjp { margin-top: 8px; }
.cjp--confirm {
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(80, 211, 252, 0.25);
  background: var(--gradient-brand-soft);
}
.cjp__title { font-size: 13px; font-weight: 600; color: var(--surface-heading); }
.cjp__text { font-size: 12px; color: var(--surface-text); margin-top: 6px; line-height: 1.5; }
.cjp__meta, .cjp__sub { font-size: 11px; color: var(--surface-muted); line-height: 1.4; }
.cjp__sub { margin-top: 2px; }

.cjp__chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.cjp__chip {
  font-size: 11px; font-weight: 600; padding: 2px 8px;
  border-radius: var(--radius-pill); background: var(--surface-2); color: var(--surface-text);
}
.cjp__chip--new, .cjp__chip--changed { color: var(--brand-cyan); }
.cjp__chip--error, .cjp__chip--removed { color: var(--status-warning); }

.cjp__actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.cjp__btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border-radius: var(--radius-pill);
  border: 1px solid var(--surface-3); background: none;
  font-size: 12px; font-weight: 600; color: var(--surface-text); cursor: pointer;
}
.cjp__btn--primary { border: none; background: var(--gradient-brand); color: #fff; }
.cjp__btn:disabled { opacity: 0.45; cursor: not-allowed; }

.cjp__bar { height: 4px; border-radius: var(--radius-pill); background: var(--surface-2); overflow: hidden; }
.cjp__bar-fill { height: 100%; background: var(--gradient-brand); transition: width var(--t-slow); }

.cjp__toggle {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  border: none; background: none; padding: 0; cursor: pointer;
  font-size: 12px; font-weight: 600; color: var(--surface-text); text-align: left;
}
.cjp__toggle-meta { font-weight: 400; color: var(--surface-muted); }
.cjp__warn-count { color: var(--status-warning); }

.cjp__report { margin-top: 10px; display: grid; gap: 14px; }
.cjp__h {
  font-size: 11px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  color: var(--surface-muted); margin-bottom: 6px;
}
.cjp__list { display: grid; gap: 8px; font-size: 12px; color: var(--surface-text); }
.cjp__link { color: var(--surface-heading); text-decoration: none; overflow-wrap: anywhere; }
.cjp__link:hover { text-decoration: underline; }
.cjp__badge {
  display: inline-block; min-width: 26px; text-align: center; margin-right: 6px;
  font-size: 10px; font-weight: 700; padding: 1px 5px;
  border-radius: var(--radius-pill); background: var(--surface-2); color: var(--surface-text);
}
.cjp__badge--mid { color: var(--brand-cyan); }
.cjp__badge--high { background: var(--gradient-brand); color: #fff; }
.cjp__expired {
  margin-left: 6px; font-size: 10px; font-weight: 700; padding: 1px 6px;
  border-radius: var(--radius-pill); background: rgba(245, 158, 11, 0.15); color: var(--status-warning);
}
.cjp__warn-icon { color: var(--status-warning); margin-right: 4px; }
</style>
