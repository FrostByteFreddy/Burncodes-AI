<template>
  <div class="alog">
    <p class="alog__title">{{ $t('knowledge.log.title') }}</p>
    <ol v-if="rows.length" ref="listEl" class="alog__list" aria-live="polite">
      <li v-for="row in rows" :key="row.id" class="alog__row" :class="`alog__row--${row.state}`">
        <span class="alog__icon">
          <font-awesome-icon v-if="row.state === 'running'" :icon="['fas', 'spinner']" class="animate-spin" />
          <font-awesome-icon v-else-if="row.state === 'failed'" :icon="['fas', 'triangle-exclamation']" />
          <font-awesome-icon v-else-if="row.state === 'done'" :icon="['fas', 'check']" />
          <font-awesome-icon v-else :icon="['fas', 'circle']" class="alog__dot" />
        </span>
        <span class="alog__text">{{ row.text }}</span>
        <time class="alog__time" :datetime="row.created_at">{{ fmtTime(row.created_at) }}</time>
      </li>
    </ol>
    <p v-else class="alog__empty">{{ $t('knowledge.log.empty') }}</p>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  entries: { type: Array, default: () => [] },
  // newest N rows shown; the list scrolls for more
  limit: { type: Number, default: 40 },
});
const { t, locale } = useI18n();
const listEl = ref(null);

// "page" label for a URL: last path segment (decoded) or host
const pageLabel = (data) => {
  if (data.title) return data.title;
  try {
    const u = new URL(data.url);
    const last = u.pathname.split('/').filter(Boolean).pop();
    return last ? decodeURIComponent(last) : u.host;
  } catch { return data.url || ''; }
};

// Start events are folded into their finishing event so each item is one row
const FINISHES = { scan: ['scanned'], learn_source: ['learned', 'learn_failed'] };

const rows = computed(() => {
  const finished = new Map();   // `${kind}:${url}` -> finishing entry
  for (const e of props.entries) {
    for (const [start, ends] of Object.entries(FINISHES)) {
      if (ends.includes(e.event)) finished.set(`${start}:${e.data?.url}`, e);
    }
  }
  const out = [];
  for (const e of props.entries) {
    const d = e.data || {};
    if (Object.values(FINISHES).flat().includes(e.event)) continue; // rendered via their start event
    let entry = e;
    let state = 'info';
    if (FINISHES[e.event]) {
      const end = finished.get(`${e.event}:${d.url}`);
      entry = end || e;
      state = !end ? 'running'
        : end.event === 'learn_failed' || ['error', 'refused'].includes(end.data?.outcome) ? 'failed'
        : 'done';
    } else if (e.event === 'job_done' || e.event === 'scan_done') {
      state = 'done';
    }
    out.push({ id: e.id, created_at: entry.created_at, state, text: format(entry) });
  }
  return out.slice(-props.limit);
});

function format(e) {
  const d = e.data || {};
  const page = pageLabel(d);
  switch (e.event) {
    case 'job_started':  return t('knowledge.log.job_started');
    case 'scan':         return t('knowledge.log.scan', { page });
    case 'scanned':      return t('knowledge.log.scanned', { page, outcome: t(`knowledge.estimate.${d.outcome}`, d.outcome || '') });
    case 'links_found':  return t('knowledge.log.links_found', { page, count: d.count });
    case 'scan_done':    return t('knowledge.log.scan_done', { n: d.to_learn, cost: fmtChf(d.cost_chf) });
    case 'learn_start':  return t('knowledge.log.learn_start', { n: d.count });
    case 'learn_source': return t('knowledge.log.learn_source', { page });
    case 'learned':      return t('knowledge.log.learned', { page, sections: d.sections, facts: d.facts, dates: d.dates });
    case 'learn_failed': return t('knowledge.log.learn_failed', { page, reason: d.reason });
    case 'job_done':     return t('knowledge.log.job_done', { n: d.learned, cost: fmtChf(d.cost_chf) });
    default:             return e.event;
  }
}

const fmtChf = (v) => Number(v || 0).toFixed(2);
const fmtTime = (iso) => new Date(iso).toLocaleTimeString(locale.value, { hour: '2-digit', minute: '2-digit', second: '2-digit' });

// Keep the newest row in view while the user hasn't scrolled up
watch(() => rows.value.length, async () => {
  const el = listEl.value;
  if (!el) return;
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  await nextTick();
  if (atBottom) el.scrollTop = el.scrollHeight;
});
</script>

<style scoped>
.alog { display: flex; flex-direction: column; gap: 8px; }
.alog__title {
  font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--surface-muted);
}
.alog__list {
  max-height: 220px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px; border-radius: var(--radius-md);
  background: var(--surface-0); border: 1px solid var(--surface-3);
  font-size: 12px;
}
.alog__row {
  display: grid; grid-template-columns: 18px minmax(0, 1fr) auto; align-items: baseline; gap: 8px;
  padding: 3px 4px; border-radius: var(--radius-sm); color: var(--surface-text);
}
.alog__icon { display: flex; justify-content: center; font-size: 11px; color: var(--surface-muted); }
.alog__dot { font-size: 5px; }
.alog__row--running .alog__icon { color: var(--brand-cyan); }
.alog__row--done .alog__icon { color: var(--status-success); }
.alog__row--failed .alog__icon, .alog__row--failed .alog__text { color: var(--status-warning); }
.alog__text { min-width: 0; overflow-wrap: anywhere; line-height: 1.45; }
.alog__time { font-size: 10px; color: var(--surface-muted); font-variant-numeric: tabular-nums; }
.alog__empty { font-size: 12px; color: var(--surface-muted); }
</style>
