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
      <dl class="crep__stats">
        <div v-for="s in stats" :key="s.label" class="crep__stat">
          <dt>{{ s.label }}</dt>
          <dd>{{ s.value }}</dd>
        </div>
      </dl>

      <h3 class="crep__h">{{ $t('knowledge.report.important') }}</h3>
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
      <p v-if="!issues.length" class="crep__muted">{{ $t('knowledge.report.noReview') }}</p>
      <IssueList v-else :issues="issues" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import IssueList from './IssueList.vue';

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
// reports from before 2026-10-25 carry free-text warnings; only structured issues are shown
const issues = computed(() => (props.report.attention || []).filter((a) => a.kind));

const reviewCount = computed(() => issues.value.length);
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

// HTTP codes in words: municipal staff don't read "204"
const CODE_KIND = (code) => {
  const n = Number(code);
  if (n === 204) return 'empty';
  if (n === 404 || n === 410) return 'notFound';
  if (n === 401 || n === 403) return 'blocked';
  if (n === 408 || n === 0) return 'timeout';
  if (n === 429 || n === 503) return 'limited';
  if (n >= 500) return 'serverError';
  return 'other';
};
const unreachable = computed(() => {
  const byKind = {};
  for (const [code, n] of Object.entries(props.report.errors || {})) {
    const kind = CODE_KIND(code);
    byKind[kind] = (byKind[kind] || 0) + n;
  }
  return Object.entries(byKind).map(([kind, n]) => t(`knowledge.report.codes.${kind}`, { n }, n)).join(', ');
});

const fmtDay = (iso) => (iso
  ? new Date(`${iso}T00:00:00`).toLocaleDateString(locale.value, { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' })
  : '');
</script>

<style scoped>
.crep { display: flex; flex-direction: column; gap: 20px; }

.crep__tabs {
  display: inline-flex; gap: 4px; padding: 4px; align-self: flex-start;
  border-radius: var(--radius-pill); background: var(--surface-2);
}
.crep__tab {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 16px; border: none; border-radius: var(--radius-pill);
  background: none; color: var(--surface-muted);
  font-size: var(--text-sm); font-weight: 600; cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast);
}
.crep__tab:hover { color: var(--surface-heading); }
.crep__tab--active { background: var(--interactive-strong); color: var(--on-interactive); }
.crep__tab-count {
  font-size: var(--text-xs); font-weight: 700; padding: 0 8px; border-radius: var(--radius-pill);
  background: var(--surface-3); color: var(--surface-text);
}
.crep__tab--active .crep__tab-count { background: var(--interactive-soft); color: var(--interactive); }
.crep__tab-count--warn { background: var(--status-warning-soft); color: var(--status-warning); }

.crep__panel { display: flex; flex-direction: column; gap: 16px; }

/* Counts read as one line of figures, label after the number */
.crep__stats { display: flex; flex-wrap: wrap; gap: 8px 28px; margin: 0; }
.crep__stat { display: flex; flex-direction: row-reverse; align-items: baseline; gap: 8px; }
.crep__stat dt { font-size: var(--text-sm); color: var(--surface-muted); }
.crep__stat dd { margin: 0; font-size: var(--text-lg); font-weight: 700; color: var(--surface-heading); }

.crep__h { font-size: 16px; font-weight: 700; color: var(--surface-heading); margin-top: 4px; }
.crep__list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 12px; }
.crep__item { display: grid; grid-template-columns: 88px minmax(0, 1fr); gap: 12px; align-items: baseline; }
.crep__item-body { min-width: 0; }
.crep__level { font-size: var(--text-xs); font-weight: 700; }
.crep__level--high { color: var(--interactive); }
.crep__level--mid { color: var(--surface-muted); }

.crep__link, .crep__doc {
  color: var(--surface-heading); font-size: 16px; font-weight: 600; text-decoration: none; overflow-wrap: anywhere;
}
.crep__link:hover, .crep__doc:hover { color: var(--interactive); text-decoration: underline; }
.crep__link-icon { font-size: 10px; margin-left: 8px; opacity: 0.5; }
.crep__muted { font-size: var(--text-sm); color: var(--surface-muted); line-height: var(--leading-body); margin-top: 2px; max-width: var(--measure); }
.crep__unreachable { margin-top: 4px; }

.crep__group { display: flex; flex-direction: column; gap: 8px; }
.crep__group + .crep__group { margin-top: 8px; }
.crep__doc { display: inline-flex; align-items: center; gap: 8px; }
.crep__doc-icon { color: var(--surface-muted); font-size: 14px; }

.crep__table { border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--surface-3); }
.crep__tr {
  display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1.4fr) 64px; gap: 12px;
  padding: 8px 16px; font-size: var(--text-sm); color: var(--surface-text);
  border-top: 1px solid var(--surface-3);
}
.crep__tr:first-child { border-top: none; }
.crep__tr--head { background: var(--surface-2); font-size: var(--text-xs); font-weight: 600; color: var(--surface-muted); }
.crep__tr--expired { color: var(--surface-muted); }
.crep__series { font-weight: 600; overflow-wrap: anywhere; }
.crep__tr--expired .crep__series { font-weight: 500; }
.crep__zone {
  margin-left: 8px; font-size: var(--text-xs); font-weight: 600; padding: 1px 8px;
  border-radius: var(--radius-pill); background: var(--surface-2); color: var(--surface-text);
}
.crep__num { text-align: right; }
.crep__expired { color: var(--surface-muted); }


@media (max-width: 640px) {
  .crep__tabs { align-self: stretch; overflow-x: auto; }
  .crep__item { grid-template-columns: minmax(0, 1fr); gap: 2px; }
  .crep__tr { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 40px; padding: 8px 8px; }
}
</style>
