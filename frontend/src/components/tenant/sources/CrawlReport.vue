<template>
  <div class="crep">
    <div class="crep__tabs" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        role="tab"
        class="crep__tab"
        :class="{ 'crep__tab--active': active === tab.key }"
        :aria-selected="active === tab.key"
        @click="active = tab.key"
      >
        {{ tab.label }}
        <span v-if="tab.count" class="crep__tab-count" :class="{ 'crep__tab-count--warn': tab.key === 'review' }">{{ tab.count }}</span>
      </button>
    </div>

    <!-- Overview -->
    <div v-if="active === 'overview'" class="crep__panel">
      <div class="crep__stats">
        <div v-for="s in stats" :key="s.label" class="crep__stat">
          <p class="crep__stat-label">{{ s.label }}</p>
          <p class="crep__stat-value">{{ s.value }}</p>
        </div>
      </div>

      <p class="crep__h">{{ $t('knowledge.report.important') }}</p>
      <ul v-if="report.highlights?.length" class="crep__list">
        <li v-for="h in report.highlights" :key="h.source_id" class="crep__item">
          <span class="crep__level" :class="h.importance >= 85 ? 'crep__level--high' : 'crep__level--mid'">
            {{ h.importance >= 85 ? $t('knowledge.report.high') : $t('knowledge.report.medium') }}
          </span>
          <div class="crep__item-body">
            <a :href="h.url" target="_blank" rel="noopener noreferrer" class="crep__link">
              {{ h.title }}
              <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="crep__link-icon" />
            </a>
            <p class="crep__muted">{{ h.reason }}</p>
          </div>
        </li>
      </ul>
      <p v-else class="crep__muted">{{ $t('knowledge.report.noImportant') }}</p>
      <p v-if="unreachable" class="crep__muted crep__unreachable">{{ $t('knowledge.report.unreachable', { list: unreachable }) }}</p>
    </div>

    <!-- Dates, grouped by document -->
    <div v-else-if="active === 'dates'" class="crep__panel">
      <p v-if="!dateGroups.length" class="crep__muted">{{ $t('knowledge.report.noDates') }}</p>
      <section v-for="g in dateGroups" :key="g.source_id" class="crep__group">
        <a :href="g.url" target="_blank" rel="noopener noreferrer" class="crep__doc">
          <font-awesome-icon :icon="['fas', 'file-lines']" class="crep__doc-icon" />
          {{ g.title }}
          <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="crep__link-icon" />
        </a>
        <div class="crep__table" role="table">
          <div class="crep__tr crep__tr--head" role="row">
            <span role="columnheader">{{ $t('knowledge.report.series') }}</span>
            <span role="columnheader">{{ $t('knowledge.report.next') }}</span>
            <span role="columnheader" class="crep__num">{{ $t('knowledge.report.count') }}</span>
          </div>
          <div v-for="s in g.items" :key="`${s.series}-${s.zone}`" class="crep__tr" :class="{ 'crep__tr--expired': s.ended }" role="row">
            <span role="cell" class="crep__series">
              {{ s.series }}<span v-if="s.zone" class="crep__zone">{{ s.zone }}</span>
            </span>
            <span role="cell">
              <template v-if="s.next">{{ fmtDay(s.next) }}</template>
              <span v-else-if="s.ended" class="crep__expired">{{ $t('knowledge.report.expired', { date: fmtDay(s.last) }) }}</span>
              <template v-else>{{ $t('knowledge.report.until', { date: fmtDay(s.last) }) }}</template>
            </span>
            <span role="cell" class="crep__num">{{ s.count }}</span>
          </div>
        </div>
      </section>
    </div>

    <!-- To review, grouped by document -->
    <div v-else class="crep__panel">
      <p v-if="!reviewGroups.length" class="crep__muted">{{ $t('knowledge.report.noReview') }}</p>
      <section v-for="g in reviewGroups" :key="g.source_id" class="crep__group">
        <a :href="g.url" target="_blank" rel="noopener noreferrer" class="crep__doc">
          <font-awesome-icon :icon="['fas', 'file-lines']" class="crep__doc-icon" />
          {{ g.title }}
          <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="crep__link-icon" />
        </a>
        <ul class="crep__list">
          <li v-for="(m, i) in g.items" :key="i" class="crep__warn">
            <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="crep__warn-icon" />
            <span>{{ m }}</span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({ report: { type: Object, required: true } });
const { t, locale } = useI18n();
const active = ref('overview');

const groupBy = (items, map) => {
  const groups = new Map();
  for (const it of items || []) {
    if (!groups.has(it.source_id)) groups.set(it.source_id, { source_id: it.source_id, title: it.title, url: it.url, items: [] });
    groups.get(it.source_id).items.push(map(it));
  }
  return [...groups.values()];
};

// Reports written before `next` existed only carry first/last — derive "ended" from the last date then
const todayIso = new Date().toISOString().slice(0, 10);
const dateGroups = computed(() =>
  groupBy(props.report.schedules, (s) => ({ ...s, ended: s.next ? false : s.last < todayIso })).map((g) => ({
    ...g,
    // upcoming first (by next date), then ended series
    items: g.items.sort((a, b) => (a.ended - b.ended) || String(a.next || a.last).localeCompare(String(b.next || b.last))),
  }))
);
const reviewGroups = computed(() => groupBy(props.report.attention, (a) => a.message));

const reviewCount = computed(() => (props.report.attention || []).length);
const tabs = computed(() => [
  { key: 'overview', label: t('knowledge.report.overview') },
  { key: 'dates', label: t('knowledge.report.dates'), count: (props.report.schedules || []).length },
  { key: 'review', label: t('knowledge.report.review'), count: reviewCount.value },
]);

const stats = computed(() => {
  const c = props.report.counts || {};
  return [
    { label: t('knowledge.report.learned'), value: c.learned || 0 },
    { label: t('knowledge.report.unchanged'), value: c.unchanged || 0 },
    { label: t('knowledge.report.removed'), value: c.removed || 0 },
    { label: t('knowledge.report.errors'), value: c.errors || 0 },
    { label: t('knowledge.report.cost'), value: `CHF ${Number(props.report.cost_chf || 0).toFixed(2)}` },
  ];
});

const unreachable = computed(() =>
  Object.entries(props.report.errors || {}).map(([code, n]) => `${n}× ${code}`).join(', ')
);

const fmtDay = (iso) => (iso
  ? new Date(`${iso}T00:00:00`).toLocaleDateString(locale.value, { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' })
  : '');
</script>

<style scoped>
.crep { display: flex; flex-direction: column; gap: 16px; }

.crep__tabs {
  display: inline-flex; gap: 4px; padding: 4px; align-self: flex-start;
  border-radius: var(--radius-pill); background: var(--surface-2);
}
.crep__tab {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border: none; border-radius: var(--radius-pill);
  background: none; color: var(--surface-muted);
  font-size: 12px; font-weight: 600; cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast);
}
.crep__tab:hover { color: var(--surface-text); }
.crep__tab--active { background: var(--gradient-brand); color: #fff; }
.crep__tab-count {
  font-size: 10px; font-weight: 700; padding: 0 6px; border-radius: var(--radius-pill);
  background: var(--surface-3); color: var(--surface-text);
}
.crep__tab--active .crep__tab-count { background: rgba(255, 255, 255, 0.2); color: #fff; }
.crep__tab-count--warn { background: rgba(245, 158, 11, 0.2); color: var(--status-warning); }

.crep__panel { display: flex; flex-direction: column; gap: 14px; }

.crep__stats { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; max-width: 760px; }
.crep__stat { padding: 12px 14px; border-radius: var(--radius-md); background: var(--surface-2); }
.crep__stat-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--surface-muted); margin-bottom: 4px;
}
.crep__stat-value { font-size: 20px; font-weight: 700; color: var(--surface-heading); font-variant-numeric: tabular-nums; }

.crep__h {
  font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--surface-muted);
}
.crep__list { display: flex; flex-direction: column; gap: 10px; }
.crep__item { display: flex; gap: 12px; align-items: flex-start; }
.crep__item-body { min-width: 0; }
.crep__level {
  flex-shrink: 0; margin-top: 1px; min-width: 56px; text-align: center;
  font-size: 10px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  padding: 3px 8px; border-radius: var(--radius-pill);
}
.crep__level--high { background: var(--gradient-brand); color: #fff; }
.crep__level--mid { background: rgba(80, 211, 252, 0.12); color: var(--brand-cyan); }

.crep__link, .crep__doc {
  color: var(--surface-heading); font-size: 13px; font-weight: 600; text-decoration: none; overflow-wrap: anywhere;
}
.crep__link:hover, .crep__doc:hover { color: var(--brand-cyan); }
.crep__link-icon { font-size: 9px; margin-left: 4px; opacity: 0.5; }
.crep__muted { font-size: 12px; color: var(--surface-muted); line-height: 1.55; margin-top: 2px; }
.crep__unreachable { margin-top: 4px; }

.crep__group { display: flex; flex-direction: column; gap: 8px; }
.crep__doc { display: inline-flex; align-items: center; gap: 8px; }
.crep__doc-icon { color: var(--brand-magenta); font-size: 12px; }

.crep__table { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--surface-3); }
.crep__tr {
  display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1.4fr) 64px; gap: 12px;
  padding: 9px 14px; font-size: 12px; color: var(--surface-text);
  border-top: 1px solid var(--surface-3);
}
.crep__tr:first-child { border-top: none; }
.crep__tr--head {
  background: var(--surface-2);
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--surface-muted);
}
.crep__tr--expired { color: var(--surface-muted); }
.crep__series { font-weight: 600; overflow-wrap: anywhere; }
.crep__tr--expired .crep__series { font-weight: 500; }
.crep__zone {
  margin-left: 8px; font-size: 10px; font-weight: 700; padding: 1px 7px;
  border-radius: var(--radius-pill); background: var(--surface-2); color: var(--surface-text);
}
.crep__num { text-align: right; font-variant-numeric: tabular-nums; }
.crep__expired { color: var(--surface-muted); }

.crep__warn {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 10px 12px; border-radius: var(--radius-md);
  background: rgba(245, 158, 11, 0.06); border: 1px solid rgba(245, 158, 11, 0.18);
  font-size: 12px; line-height: 1.55; color: var(--surface-text);
}
.crep__warn-icon { color: var(--status-warning); margin-top: 3px; flex-shrink: 0; }

@media (max-width: 640px) {
  .crep__stats { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .crep__tabs { align-self: stretch; overflow-x: auto; }
  .crep__tr { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 40px; padding: 8px 10px; }
}
</style>
