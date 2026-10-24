<template>
  <div class="ko">
    <!-- The dates the chatbot can answer in the next two weeks -->
    <section class="ko-strip" :aria-label="$t('knowledge.overview.stripTitle')">
      <div class="ko-strip__head">
        <h2 class="panel-title">{{ $t('knowledge.overview.stripTitle') }}</h2>
        <p class="panel-sub">{{ $t('knowledge.overview.stripSub') }}</p>
      </div>

      <div v-if="loading && !data" class="ko-strip__skeleton"></div>
      <p v-else-if="!data?.upcoming?.length" class="ko-strip__empty">
        {{ data?.ended?.length ? $t('knowledge.overview.noneUpcomingEnded') : $t('knowledge.overview.noneUpcoming') }}
      </p>

      <ol v-else class="ko-days">
        <li
          v-for="day in days"
          :key="day.iso"
          class="ko-day"
          :class="{ 'ko-day--today': day.isToday, 'ko-day--weekend': day.isWeekend, 'ko-day--empty': !day.events.length }"
        >
          <p class="ko-day__weekday">{{ day.weekday }}</p>
          <p class="ko-day__date"><span class="ko-day__num">{{ day.num }}</span><span class="ko-day__month">{{ day.month }}</span></p>
          <ul v-if="day.events.length" class="ko-day__events">
            <li v-for="(e, i) in day.events" :key="i" class="ko-event" :class="{ 'ko-event--moved': e.is_exception }">
              <span class="ko-event__series">{{ e.series }}</span>
              <span v-if="e.zone" class="ko-event__zone">{{ e.zone }}</span>
              <span v-if="e.is_exception" class="ko-event__moved">{{ $t('knowledge.overview.moved') }}</span>
            </li>
          </ul>
        </li>
      </ol>
    </section>

    <!-- What needs a person -->
    <section class="ko-needs panel" :aria-label="$t('knowledge.overview.needsTitle')">
      <div class="ko-needs__head">
        <h2 class="panel-title">
          {{ $t('knowledge.overview.needsTitle') }}
          <span v-if="needsCount" class="ko-needs__count">{{ needsCount }}</span>
        </h2>
      </div>

      <p v-if="!needsCount" class="ko-needs__none">
        <font-awesome-icon :icon="['fas', 'check']" class="ko-needs__ok" />
        {{ $t('knowledge.overview.needsNone') }}
      </p>

      <ul v-else class="ko-needs__list">
        <li v-for="s in data.ended" :key="`ended-${s.series}-${s.zone}`" class="ko-need">
          <font-awesome-icon :icon="['fas', 'calendar-xmark']" class="ko-need__icon" />
          <div>
            <p class="ko-need__text">{{ $t('knowledge.overview.ended', { series: s.zone ? `${s.series} (${s.zone})` : s.series, date: fmtDay(s.last) }) }}</p>
            <p class="meta">{{ $t('knowledge.overview.endedHint') }}</p>
          </div>
        </li>
        <li v-for="group in issueGroups" :key="group.source_id" class="ko-need">
          <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="ko-need__icon" />
          <div>
            <a :href="group.url" target="_blank" rel="noopener noreferrer" class="ko-need__doc">{{ group.title }}</a>
            <ul class="ko-need__messages">
              <li v-for="(m, i) in group.messages" :key="i">{{ m }}</li>
            </ul>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';

const props = defineProps({
  tenantId: { type: String, required: true },
  // bump to reload (e.g. after a crawl finished)
  refreshKey: { type: Number, default: 0 },
});
const { locale } = useI18n();

const data = ref(null);
const loading = ref(false);

const load = async () => {
  if (!props.tenantId) return;
  loading.value = true;
  try {
    const r = await apiClient.get(`/tenants/${props.tenantId}/knowledge/overview`, { params: { days: 14 } });
    data.value = r.data;
  } catch { /* overview is supplementary */ }
  finally { loading.value = false; }
};
watch(() => [props.tenantId, props.refreshKey], load, { immediate: true });

const days = computed(() => {
  if (!data.value) return [];
  const start = new Date(`${data.value.today}T00:00:00`);
  const byDay = new Map();
  for (const e of data.value.upcoming || []) {
    if (!byDay.has(e.event_date)) byDay.set(e.event_date, []);
    byDay.get(e.event_date).push(e);
  }
  return Array.from({ length: data.value.days || 14 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    return {
      iso,
      isToday: i === 0,
      isWeekend: d.getDay() === 0 || d.getDay() === 6,
      weekday: d.toLocaleDateString(locale.value, { weekday: 'short' }),
      num: d.getDate(),
      month: d.toLocaleDateString(locale.value, { month: 'short' }),
      events: byDay.get(iso) || [],
    };
  });
});

const issueGroups = computed(() => {
  const groups = new Map();
  for (const it of data.value?.issues || []) {
    if (!groups.has(it.source_id)) groups.set(it.source_id, { source_id: it.source_id, title: it.title, url: it.url, messages: [] });
    groups.get(it.source_id).messages.push(it.message);
  }
  return [...groups.values()];
});
const needsCount = computed(() => (data.value?.ended?.length || 0) + issueGroups.value.length);

const fmtDay = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString(locale.value, { day: 'numeric', month: 'long', year: 'numeric' });

defineExpose({ reload: load });
</script>

<style scoped>
.ko { display: flex; flex-direction: column; gap: 20px; }

/* ── Date strip: the page's one strong element ───────────────────── */
.ko-strip {
  padding: 24px 24px 20px;
  border-radius: var(--radius-xl);
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
}
.ko-strip__head { margin-bottom: 18px; }
.ko-strip__empty { font-size: 15px; color: var(--surface-muted); max-width: var(--measure); }
.ko-strip__skeleton { height: 150px; border-radius: var(--radius-lg); background: var(--surface-2); }

/* Two weeks as two rows of seven days — the shape of a printed collection calendar */
.ko-days {
  list-style: none; padding: 0;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  border-top: 1px solid var(--surface-3);
}
.ko-day {
  min-height: 118px;
  padding: 12px 12px 14px;
  border-left: 1px solid var(--surface-3);
  border-bottom: 1px solid var(--surface-3);
  position: relative;
  min-width: 0;
}
.ko-day:nth-child(7n + 1) { border-left: none; }
.ko-day:nth-last-child(-n + 7) { border-bottom: none; }
.ko-day--weekend { background: rgba(17, 21, 45, 0.45); }
.ko-day--today::before {
  content: ''; position: absolute; left: 0; right: 0; top: -1px; height: 3px;
  background: var(--interactive);
}
.ko-day__weekday { font-size: var(--text-xs); font-weight: 600; color: var(--surface-muted); }
.ko-day--today .ko-day__weekday { color: var(--interactive); }
.ko-day__date { display: flex; align-items: baseline; gap: 4px; margin: 2px 0 10px; }
.ko-day__num { font-size: var(--text-2xl); font-weight: 800; line-height: 1; color: var(--surface-heading); letter-spacing: -0.02em; }
.ko-day--empty .ko-day__num { color: var(--surface-3); }
.ko-day__month { font-size: var(--text-xs); color: var(--surface-muted); }

.ko-day__events { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.ko-event {
  display: flex; flex-direction: column; gap: 2px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  background: var(--interactive-soft);
  border-left: 2px solid var(--interactive);
}
.ko-event--moved { background: var(--status-warning-soft); border-left-color: var(--status-warning); }
.ko-event__series { font-size: 13px; font-weight: 700; color: var(--surface-heading); line-height: 1.25; hyphens: auto; overflow-wrap: break-word; }
.ko-event__zone { font-size: var(--text-xs); color: var(--surface-text); }
.ko-event__moved { font-size: var(--text-xs); font-weight: 700; color: var(--status-warning); }

/* ── Needs you ───────────────────────────────────────────────────── */
.ko-needs__head { margin-bottom: 14px; }
.ko-needs__head .panel-title { display: flex; align-items: center; gap: 10px; }
.ko-needs__count {
  font-size: 13px; font-weight: 800; min-width: 24px; padding: 1px 8px; text-align: center;
  border-radius: var(--radius-pill); background: var(--status-warning); color: var(--surface-0);
}
.ko-needs__none { display: flex; align-items: center; gap: 10px; font-size: 15px; color: var(--surface-text); }
.ko-needs__ok { color: var(--status-success); }
.ko-needs__list { list-style: none; padding: 0; display: flex; flex-direction: column; }
.ko-need {
  display: grid; grid-template-columns: 20px minmax(0, 1fr); gap: 12px;
  padding: 14px 0; border-top: 1px solid var(--surface-3);
}
.ko-need:first-child { border-top: none; padding-top: 0; }
.ko-need__icon { margin-top: 3px; color: var(--status-warning); }
.ko-need__text { font-size: 15px; color: var(--surface-heading); font-weight: 600; max-width: var(--measure); }
.ko-need__doc { font-size: 15px; font-weight: 700; color: var(--surface-heading); text-decoration: none; }
.ko-need__doc:hover { color: var(--interactive); text-decoration: underline; }
.ko-need__messages { margin-top: 6px; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; max-width: var(--measure); }
.ko-need__messages li { font-size: var(--text-sm); color: var(--surface-text); line-height: var(--leading-body); }

/* Phones: one day per row, empty days collapse to a single line */
@media (max-width: 760px) {
  .ko-strip { padding: 18px 16px 14px; }
  .ko-days { grid-template-columns: 1fr; }
  .ko-day { min-height: 0; display: grid; grid-template-columns: 64px 1fr; gap: 4px 12px; border-left: none; padding: 10px 0; }
  .ko-day:nth-last-child(-n + 7) { border-bottom: 1px solid var(--surface-3); }
  .ko-day:last-child { border-bottom: none; }
  .ko-day__weekday { grid-column: 1; }
  .ko-day__date { grid-column: 1; margin: 0; }
  .ko-day__events { grid-column: 2; grid-row: 1 / span 2; }
  .ko-day__num { font-size: var(--text-lg); }
  .ko-day--today::before { right: auto; bottom: 0; width: 3px; height: auto; left: -16px; }
}
</style>
