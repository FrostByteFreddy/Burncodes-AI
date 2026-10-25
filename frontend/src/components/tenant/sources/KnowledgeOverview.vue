<template>
  <div class="ko">
    <!-- The dates the chatbot can answer in the next two weeks -->
    <section class="ko-strip" :aria-label="$t('knowledge.overview.stripTitle')">
      <div class="ko-strip__head">
        <h2 class="panel-title">{{ $t('knowledge.overview.stripTitle') }}</h2>
        <p class="panel-sub">{{ $t('knowledge.overview.stripSub') }}</p>
      </div>

      <ol v-if="loading && !data" class="ko-days" aria-busy="true">
        <li v-for="n in 14" :key="n" class="ko-day">
          <span class="ghost ghost--line" style="width: 28px; height: 10px"></span>
          <span class="ghost" style="width: 36px; height: 24px; margin: 6px 0 10px"></span>
          <span v-if="n % 3 === 1" class="ghost" style="height: 34px"></span>
        </li>
      </ol>
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

      <!-- The same dates as calendars residents can subscribe to -->
      <div class="ko-cal">
        <div class="ko-cal__row">
          <div>
            <label for="ko-cal" class="ko-cal__title">{{ $t('knowledge.calendars.title') }}</label>
            <p class="meta">{{ $t('knowledge.calendars.sub') }}</p>
          </div>
          <input id="ko-cal" type="checkbox" role="switch" class="ko-switch" :checked="calendarsOn" :disabled="savingCal" @change="setCalendars($event.target.checked)" />
        </div>
        <p v-if="tenant?.test_protected && calendarsOn" class="meta ko-cal__warn">{{ $t('knowledge.calendars.protected') }}</p>
        <ul v-else-if="calendarsOn && feeds.length" class="ko-cal__list">
          <li v-for="f in feeds" :key="f.key" class="ko-cal__feed">
            <span class="ko-cal__name">{{ f.zone ? `${f.series} (${f.zone})` : f.series }}</span>
            <span class="meta">{{ $t('knowledge.calendars.dates', { n: f.count }) }}</span>
            <button type="button" class="ko-cal__copy" @click="copyFeed(f)">
              <font-awesome-icon :icon="['fas', copied === f.key ? 'check' : 'link']" /> {{ copied === f.key ? $t('knowledge.calendars.copied') : $t('knowledge.calendars.copy') }}
            </button>
          </li>
        </ul>
      </div>
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

      <ul v-else-if="data.ended?.length" class="ko-needs__list">
        <li v-for="s in data.ended" :key="`ended-${s.series}-${s.zone}`" class="ko-need">
          <font-awesome-icon :icon="['fas', 'calendar-xmark']" class="ko-need__icon" />
          <div>
            <p class="ko-need__text">{{ $t('knowledge.overview.ended', { series: s.zone ? `${s.series} (${s.zone})` : s.series, date: fmtDay(s.last) }) }}</p>
            <p class="meta">{{ $t('knowledge.overview.endedHint') }}</p>
          </div>
        </li>
      </ul>
      <IssueList v-if="issues.length" :issues="issues" class="ko-needs__issues" />
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useTenantsStore } from '@/stores/tenants';
import { useToast } from '@/composables/useToast';
import IssueList from './IssueList.vue';

const props = defineProps({
  tenantId: { type: String, required: true },
  // bump to reload (e.g. after a crawl finished)
  refreshKey: { type: Number, default: 0 },
});
const { t, locale } = useI18n();

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

// only structured issues; free-text warnings from before 2026-10-25 are filtered out server-side
const issues = computed(() => (data.value?.issues || []).filter((i) => i.kind));
const needsCount = computed(() => (data.value?.ended?.length || 0) + issues.value.length);

// ── Calendar feeds ──────────────────────────────────────────────────
const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const tenant = computed(() => tenantsStore.currentTenant);
const calendarsOn = computed(() => tenant.value?.calendar_feeds !== false);
const feeds = ref([]);
const savingCal = ref(false);
const copied = ref(null);

const loadFeeds = async () => {
  if (!props.tenantId) return;
  try { feeds.value = (await apiClient.get(`/calendar/${props.tenantId}`)).data.feeds || []; }
  catch { feeds.value = []; }
};
watch(() => [props.tenantId, props.refreshKey, calendarsOn.value], loadFeeds, { immediate: true });

const setCalendars = async (on) => {
  savingCal.value = true;
  try {
    await apiClient.put(`/tenants/${props.tenantId}`, { calendar_feeds: on });
    await tenantsStore.refetch(props.tenantId);
    addToast(on ? t('knowledge.calendars.on') : t('knowledge.calendars.off'), 'success');
  } catch { addToast(t('tenant.settings.actions.saveFailed'), 'error'); }
  finally { savingCal.value = false; }
};
const copyFeed = async (f) => {
  try {
    await navigator.clipboard.writeText(f.https);
    copied.value = f.key;
    setTimeout(() => { copied.value = null; }, 2000);
  } catch { addToast(t('testPage.link.copyFailed'), 'error'); }
};

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

/* ── Calendars ───────────────────────────────────────────────────── */
.ko-cal { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--surface-3); }
.ko-cal__row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.ko-cal__title { font-size: 15px; font-weight: 700; color: var(--surface-heading); cursor: pointer; }
.ko-cal__warn { margin-top: 8px; color: var(--status-warning); }
.ko-cal__list { list-style: none; padding: 0; margin: 12px 0 0; display: flex; flex-wrap: wrap; gap: 8px; }
.ko-cal__feed { display: inline-flex; align-items: center; gap: 10px; padding: 6px 6px 6px 12px; border-radius: var(--radius-md); background: var(--surface-2); }
.ko-cal__name { font-size: var(--text-sm); font-weight: 700; color: var(--surface-heading); }
.ko-cal__copy { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: var(--radius-sm); border: 1px solid var(--surface-3); background: none; color: var(--surface-text); font: inherit; font-size: var(--text-xs); font-weight: 600; cursor: pointer; }
.ko-cal__copy:hover { color: var(--surface-heading); border-color: var(--surface-muted); }
.ko-switch {
  appearance: none; flex-shrink: 0; position: relative; cursor: pointer;
  width: 44px; height: 24px; border-radius: var(--radius-pill); background: var(--surface-3); transition: background var(--t-fast);
}
.ko-switch::after { content: ''; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: var(--surface-heading); transition: transform var(--t-fast); }
.ko-switch:checked { background: var(--interactive-strong); }
.ko-switch:checked::after { transform: translateX(20px); }
.ko-switch:focus-visible { box-shadow: var(--focus-ring); }
.ko-switch:disabled { opacity: 0.5; }

/* ── Needs you ───────────────────────────────────────────────────── */
.ko-needs__head { margin-bottom: 14px; }
.ko-needs__head .panel-title { display: flex; align-items: center; gap: 10px; }
.ko-needs__count {
  font-size: 13px; font-weight: 800; min-width: 24px; padding: 1px 8px; text-align: center;
  border-radius: var(--radius-pill); background: var(--status-warning); color: var(--surface-0);
}
.ko-needs__none { display: flex; align-items: center; gap: 10px; font-size: 15px; color: var(--surface-text); }
.ko-needs__ok { color: var(--status-success); }
.ko-needs__issues { margin-top: 18px; }
.ko-needs__list { list-style: none; padding: 0; display: flex; flex-direction: column; }
.ko-need {
  display: grid; grid-template-columns: 20px minmax(0, 1fr); gap: 12px;
  padding: 14px 0; border-top: 1px solid var(--surface-3);
}
.ko-need:first-child { border-top: none; padding-top: 0; }
.ko-need__icon { margin-top: 3px; color: var(--status-warning); }
.ko-need__text { font-size: 15px; color: var(--surface-heading); font-weight: 600; max-width: var(--measure); }

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
