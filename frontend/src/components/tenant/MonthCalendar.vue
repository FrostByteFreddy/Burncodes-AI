<template>
  <div class="mc">
    <BcPageHeader :title="$t('knowledge.month.title')" :lede="$t('knowledge.month.lede')">
      <template #eyebrow>
        <router-link :to="{ name: 'TenantSources', params: { tenantId } }">{{ $t('pages.knowledgeTitle') }}</router-link> › {{ $t('knowledge.month.title') }}
      </template>
    </BcPageHeader>

    <div class="mc-bar">
      <div class="mc-bar__nav">
        <h2 class="sr-only" aria-live="polite">{{ monthLabel(month) }}</h2>
        <BcIconButton icon="chevron-left" variant="secondary" :label="$t('knowledge.month.prev')" @click="step(-1)" />
        <BcSelect v-model="pickedMonth" class="mc-bar__month" :aria-label="$t('knowledge.month.pickMonth')" :options="monthOptions" />
        <BcIconButton icon="chevron-right" variant="secondary" :label="$t('knowledge.month.next')" @click="step(1)" />
        <BcButton v-if="month !== thisMonth" size="sm" variant="ghost" @click="goTo(thisMonth)">{{ $t('knowledge.month.today') }}</BcButton>
      </div>
      <div class="mc-bar__filter">
        <div class="mc-search">
          <BcIcon name="magnifying-glass" class="mc-search__icon" />
          <Input :model-value="search" type="search" class="mc-search__input" :aria-label="$t('knowledge.month.search')" :placeholder="$t('knowledge.month.search')" @update:model-value="onType" />
        </div>
        <BcSelect v-if="summary?.series?.length" v-model="selected" class="mc-bar__select" :aria-label="$t('knowledge.month.filter')" :options="calendarOptions" />
        <BcButton v-if="activeFeed" size="sm" variant="secondary" @click="copyFeed">
          <BcIcon :name="copied ? 'check' : 'link'" />{{ copied ? $t('knowledge.calendars.copied') : $t('knowledge.calendars.copy') }}
        </BcButton>
      </div>
    </div>

    <BcNotice v-if="failed" tone="error" :title="$t('knowledge.month.loadFailed')">
      <template #actions><BcButton size="sm" variant="secondary" @click="load">{{ $t('common.retry') }}</BcButton></template>
    </BcNotice>

    <!-- Search: every date, whichever month it is in -->
    <section v-else-if="query" :aria-busy="loading" class="mc-results">
      <p class="mc-sum" role="status">
        <template v-if="loading">&nbsp;</template>
        <template v-else-if="!hits.length">{{ $t('knowledge.month.noResults', { q: query }) }}</template>
        <template v-else-if="hitTotal > results.length">{{ $t('knowledge.month.resultsCapped', { shown: results.length, n: hitTotal, q: query }) }}</template>
        <template v-else>{{ $t('knowledge.month.results', { n: hits.length, q: query }, hits.length) }}</template>
      </p>
      <ul v-if="hits.length" class="mc-list mc-list--card">
        <li v-for="(e, i) in hits" :key="i" class="mc-hit">
          <p class="mc-hit__date">{{ longDate(e.event_date) }}</p>
          <div class="mc-hit__body">
            <CalendarEntry :event="e" />
            <button type="button" class="mc-link mc-hit__show" @click="showInCalendar(e)">{{ $t('knowledge.month.showInCalendar') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <template v-else>
      <p class="mc-sum" :class="{ 'mc-sum--empty': !loading && !visible.length }">
        <template v-if="loading">&nbsp;</template>
        <template v-else-if="visible.length">{{ $t('knowledge.calendars.dates', { n: visible.length }, visible.length) }}</template>
        <template v-else>
          {{ $t(summary?.series?.length ? 'knowledge.month.noneInMonth' : 'knowledge.month.none') }}
          <button v-if="nearest" type="button" class="mc-link" @click="goTo(nearest)">{{ $t('knowledge.month.jump', { month: monthLabel(nearest) }) }}</button>
        </template>
      </p>

      <div class="mc-weekdays" aria-hidden="true"><span v-for="w in weekdays" :key="w">{{ w }}</span></div>
      <ol class="mc-grid" :aria-busy="loading" :aria-label="monthLabel(month)">
        <template v-for="cell in cells" :key="cell.key">
          <li v-if="cell.blank" class="mc-cell mc-cell--blank" aria-hidden="true"></li>
          <li v-else-if="cell.detail" id="mc-detail" class="mc-detail">
            <div class="mc-detail__head">
              <div>
                <h3 class="mc-detail__title">{{ openDay.full }}</h3>
                <p class="mc-detail__count">{{ $t('knowledge.calendars.dates', { n: openDay.events.length }, openDay.events.length) }}</p>
              </div>
              <BcIconButton icon="xmark" :label="$t('knowledge.month.closeDay')" @click="setDay(null)" />
            </div>
            <ul class="mc-list mc-list--cols">
              <li v-for="(e, i) in openDay.events" :key="i"><CalendarEntry :event="e" /></li>
            </ul>
          </li>
          <li v-else class="mc-cell" :class="{ 'mc-cell--none': !cell.day.events.length, 'mc-cell--open': cell.day.iso === openDay?.iso }">
            <button v-if="cell.day.events.length" type="button" class="mc-day" :aria-expanded="cell.day.iso === openDay?.iso" @click="setDay(cell.day.iso === openDay?.iso ? null : cell.day.iso)">
              <MonthDayLabel :day="cell.day" />
              <span class="mc-day__events">
                <span v-for="(e, i) in cell.day.events.slice(0, MAX_IN_CELL)" :key="i" class="mc-ev" :class="{ 'mc-ev--moved': e.is_exception }" :title="eventLabel(e)">
                  <span v-if="e.start_time" class="mc-ev__time">{{ e.start_time.slice(0, 5) }}</span>
                  <span class="mc-ev__name">{{ eventLabel(e) }}</span>
                  <span v-if="e.is_exception" class="sr-only">({{ $t('knowledge.overview.moved') }})</span>
                </span>
                <span v-if="cell.day.events.length > MAX_IN_CELL" class="mc-day__more">{{ $t('knowledge.month.more', { n: cell.day.events.length - MAX_IN_CELL }) }}</span>
              </span>
            </button>
            <div v-else class="mc-day mc-day--quiet">
              <MonthDayLabel :day="cell.day" />
              <Skeleton v-if="loading && cell.day.num % 4 === 1" class="mc-day__ghost" />
            </div>
          </li>
        </template>
      </ol>
      <p v-if="visible.some((e) => e.is_exception)" class="mc-legend"><span class="mc-legend__swatch" aria-hidden="true"></span>{{ $t('knowledge.month.legend') }}</p>
    </template>
  </div>
</template>

<script setup>
import { computed, h, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useToast } from '@/composables/useToast';
import CalendarEntry from './sources/CalendarEntry.vue';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { BcButton, BcIcon, BcIconButton, BcNotice, BcPageHeader, BcSelect } from '@/components/ui';

// A cell shows this many; the day view has them all
const MAX_IN_CELL = 3;

const route = useRoute();
const router = useRouter();
const { t, locale } = useI18n();
const { addToast } = useToast();
const tenantId = computed(() => route.params.tenantId);

const pad = (n) => String(n).padStart(2, '0');
const isoOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const todayIso = isoOf(new Date());
const thisMonth = todayIso.slice(0, 7);

// Month and calendar live in the address, so a reload or a shared link shows the same view
const month = computed(() => (/^\d{4}-(0[1-9]|1[0-2])$/.test(route.query.month || '') ? route.query.month : thisMonth));
const setQuery = (patch) => router.replace({ query: { ...route.query, ...patch } });
const selected = computed({
  get: () => route.query.cal || '',
  set: (cal) => setQuery({ cal: cal || undefined }),
});
// Picking a month means looking at that month, so it also ends a search
const goTo = (ym) => {
  clearTimeout(typing);
  search.value = '';
  setQuery({ month: ym === thisMonth ? undefined : ym, day: undefined, q: undefined });
};
const step = (by) => {
  const [y, m] = month.value.split('-').map(Number);
  goTo(isoOf(new Date(y, m - 1 + by, 1)).slice(0, 7));
};
const pickedMonth = computed({ get: () => month.value, set: goTo });
const setDay = (iso) => setQuery({ day: iso || undefined });

const monthLabel = (ym) => {
  const [y, m] = ym.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale.value, { month: 'long', year: 'numeric' });
};
const longDate = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString(locale.value, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
const weekdays = computed(() => Array.from({ length: 7 }, (_, i) =>
  new Date(2024, 0, 1 + i).toLocaleDateString(locale.value, { weekday: 'short' })));

// ── Data ──
const query = computed(() => String(route.query.q || '').trim());
const search = ref(String(route.query.q || ''));
let typing;
const onType = (text) => {
  search.value = text;
  clearTimeout(typing);
  typing = setTimeout(() => setQuery({ q: String(text).trim() || undefined, day: undefined }), 250);
};
watch(query, (q) => { if (q !== search.value.trim()) search.value = q; });
const results = ref([]);
const hitTotal = ref(0);
const hits = computed(() => (selected.value ? results.value.filter((e) => e.key === selected.value) : results.value));
const showInCalendar = (e) => {
  clearTimeout(typing);
  search.value = '';
  const ym = e.event_date.slice(0, 7);
  setQuery({ q: undefined, month: ym === thisMonth ? undefined : ym, day: e.event_date });
};

const events = ref([]);
const summary = ref(null);
const loading = ref(false);
const failed = ref(false);
let latest = 0;
const load = async () => {
  if (!tenantId.value) return;
  const mine = ++latest;
  loading.value = true;
  failed.value = false;
  try {
    const params = query.value
      ? { q: query.value }
      : { month: month.value, ...(summary.value ? {} : { summary: 1 }) };
    const { data } = await apiClient.get(`/tenants/${tenantId.value}/knowledge/calendar`, { params });
    if (mine !== latest) return;
    if (query.value) {
      results.value = data.results || [];
      hitTotal.value = data.total || 0;
      return;
    }
    events.value = data.events || [];
    if (data.series) summary.value = { series: data.series, months: data.months || {} };
  } catch {
    if (mine === latest) { failed.value = true; events.value = []; results.value = []; }
  } finally {
    if (mine === latest) loading.value = false;
  }
};
watch(tenantId, () => { summary.value = null; });
watch([tenantId, month, query], load, { immediate: true });

const activeSeries = computed(() => summary.value?.series?.find((s) => s.key === selected.value) || null);
const visible = computed(() => (selected.value ? events.value.filter((e) => e.key === selected.value) : events.value));
const calendarOptions = computed(() => [
  { value: '', label: t('knowledge.month.all', { n: summary.value?.series?.length || 0 }) },
  ...(summary.value?.series || []).map((s) => ({ value: s.key, label: s.zone ? `${s.series} (${s.zone})` : s.series })),
]);

// Every month with dates, and always the one on screen and the current one
const monthOptions = computed(() => {
  // The same months whatever calendar is picked; only the counts follow the filter
  const counts = activeSeries.value?.months || summary.value?.months || {};
  return [...new Set([...Object.keys(summary.value?.months || {}), month.value, thisMonth])].sort().map((m) => ({
    value: m,
    label: counts[m] ? `${monthLabel(m)} (${counts[m]})` : monthLabel(m),
  }));
});

// Nothing here: the closest month that has something
const nearest = computed(() => {
  const months = Object.keys(activeSeries.value?.months || summary.value?.months || {}).filter((m) => m !== month.value);
  const at = (ym) => { const [y, m] = ym.split('-').map(Number); return y * 12 + m; };
  return months.sort((a, b) => Math.abs(at(a) - at(month.value)) - Math.abs(at(b) - at(month.value)))[0] || null;
});

// ── Grid ──
const first = computed(() => { const [y, m] = month.value.split('-').map(Number); return new Date(y, m - 1, 1); });
const count = computed(() => new Date(first.value.getFullYear(), first.value.getMonth() + 1, 0).getDate());
const leading = computed(() => (first.value.getDay() + 6) % 7);
const trailing = computed(() => (7 - ((leading.value + count.value) % 7)) % 7);
const days = computed(() => {
  const byDay = new Map();
  for (const e of visible.value) {
    if (!byDay.has(e.event_date)) byDay.set(e.event_date, []);
    byDay.get(e.event_date).push(e);
  }
  return Array.from({ length: count.value }, (_, i) => {
    const d = new Date(first.value.getFullYear(), first.value.getMonth(), i + 1);
    const iso = isoOf(d);
    return {
      iso,
      num: i + 1,
      isToday: iso === todayIso,
      full: d.toLocaleDateString(locale.value, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }),
      // A moved date is the one people must not miss; then all-day, then by the clock
      events: [...(byDay.get(iso) || [])].sort((a, b) =>
        Number(!!b.is_exception) - Number(!!a.is_exception) || (a.start_time || '').localeCompare(b.start_time || '')),
    };
  });
});
const MonthDayLabel = (props) => h('span', { class: ['mc-day__date', props.day.isToday && 'mc-day__date--today'] }, [
  h('span', { class: 'mc-day__num', 'aria-hidden': 'true' }, String(props.day.num)),
  h('span', { class: 'mc-day__full' }, props.day.full),
]);
MonthDayLabel.props = ['day'];

const openDay = computed(() => days.value.find((d) => d.iso === route.query.day && d.events.length) || null);

// Phones list the days, so the details go right under the day; else under its week
const isPhone = ref(false);
let phoneQuery;
const readPhone = () => { isPhone.value = phoneQuery.matches; };
onMounted(() => { phoneQuery = window.matchMedia('(max-width: 720px)'); readPhone(); phoneQuery.addEventListener('change', readPhone); });
onUnmounted(() => { phoneQuery?.removeEventListener('change', readPhone); clearTimeout(typing); });

const cells = computed(() => {
  const out = [
    ...Array.from({ length: leading.value }, (_, i) => ({ key: `a${i}`, blank: true })),
    ...days.value.map((day) => ({ key: day.iso, day })),
    ...Array.from({ length: trailing.value }, (_, i) => ({ key: `z${i}`, blank: true })),
  ];
  if (openDay.value) {
    const at = leading.value + openDay.value.num - 1;
    out.splice((isPhone.value ? at : Math.floor(at / 7) * 7 + 6) + 1, 0, { key: 'detail', detail: true });
  }
  return out;
});
watch(() => openDay.value?.iso, async (iso) => {
  if (!iso) return;
  await nextTick();
  document.getElementById('mc-detail')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}, { flush: 'post' });
const eventLabel = (e) => (e.zone ? `${e.series} (${e.zone})` : e.series);

// ── The address residents subscribe to, for the calendar picked above ──
const feeds = ref([]);
watch(tenantId, async (id) => {
  if (!id) return;
  try { feeds.value = (await apiClient.get(`/calendar/${id}`)).data.feeds || []; }
  catch { feeds.value = []; }
}, { immediate: true });
const activeFeed = computed(() => feeds.value.find((f) => f.key === selected.value) || null);
const copied = ref(false);
const copyFeed = async () => {
  try {
    await navigator.clipboard.writeText(activeFeed.value.https);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch { addToast(t('testPage.link.copyFailed'), 'error'); }
};
</script>

<style scoped>
.mc-bar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px 24px; margin-bottom: 8px; }
.mc-bar__nav { display: flex; align-items: center; gap: 8px; min-width: 0; }
.mc-bar__month { width: 220px; }
.mc-bar__filter { display: flex; align-items: center; gap: 8px; min-width: 0; flex-wrap: wrap; }
.mc-bar__select { max-width: 100%; width: 240px; }
.mc-search { position: relative; width: 240px; max-width: 100%; }
.mc-search__icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--surface-text); pointer-events: none; }
.mc-search__input { padding-left: 36px; }

.mc-sum { margin: 0 0 16px; font-size: var(--text-sm); color: var(--surface-text); min-height: 20px; }
.mc-link { border: none; background: none; padding: 0; cursor: pointer; font: inherit; font-weight: 600; color: var(--interactive); text-decoration: none; }
.mc-link:hover { text-decoration: underline; }

.mc-weekdays, .mc-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
.mc-weekdays { padding-bottom: 8px; font-size: var(--text-sm); font-weight: 600; color: var(--surface-text); }
.mc-weekdays span { padding-left: 12px; }
.mc-grid { list-style: none; margin: 0; background: var(--surface-3); border-radius: var(--radius-lg); overflow: hidden; gap: 1px; border: 1px solid var(--surface-3); padding: 0; }
.mc-cell { min-width: 0; min-height: 128px; display: flex; background: var(--surface-1); }
.mc-cell--blank { background: var(--surface-0); }
.mc-day { width: 100%; min-width: 0; display: flex; flex-direction: column; gap: 8px; padding: 8px; border: none; background: none; text-align: left; font: inherit; color: inherit; }
button.mc-day { cursor: pointer; transition: background-color 120ms ease; }
button.mc-day:hover { background: var(--surface-2); }
button.mc-day:focus-visible { outline: 2px solid var(--interactive); outline-offset: -2px; }
.mc-day__ghost { height: 24px; width: 100%; }

.mc-day :deep(.mc-day__date) { display: flex; align-items: center; font-size: 14px; font-weight: 600; color: var(--surface-text); }
.mc-day :deep(.mc-day__num) { min-width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; border-radius: 999px; }
.mc-day :deep(.mc-day__date--today .mc-day__num) { background: var(--interactive); color: var(--on-interactive, #fff); }
.mc-day :deep(.mc-day__full) { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }

.mc-day__events { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.mc-ev { display: flex; align-items: baseline; gap: 4px; min-width: 0; padding: 2px 8px; border-radius: var(--radius-sm); background: var(--interactive-soft); color: var(--surface-heading); font-size: 13px; line-height: 20px; }
.mc-ev--moved { background: var(--status-warning-soft); box-shadow: inset 3px 0 0 var(--status-warning); }
.mc-ev__time { flex: none; font-weight: 700; font-variant-numeric: tabular-nums; }
/* Two lines: the zone at the end is what tells entries of one series apart */
.mc-ev__name { min-width: 0; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; line-clamp: 2; overflow: hidden; overflow-wrap: break-word; hyphens: auto; }
.mc-day__more { padding: 0 8px; font-size: 13px; line-height: 20px; font-weight: 600; color: var(--interactive); }

.mc-legend { display: flex; align-items: center; gap: 8px; margin: 12px 0 0; font-size: var(--text-sm); color: var(--surface-text); }
.mc-legend__swatch { width: 16px; height: 16px; flex: none; border-radius: var(--radius-sm); background: var(--status-warning-soft); box-shadow: inset 3px 0 0 var(--status-warning); }

.mc-cell--open { box-shadow: inset 0 0 0 2px var(--interactive); }
.mc-detail { grid-column: 1 / -1; padding: 16px; background: var(--surface-1); box-shadow: inset 0 2px 0 var(--interactive), inset 0 -2px 0 var(--interactive); }
.mc-detail__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.mc-detail__title { margin: 0; font-size: 18px; line-height: 24px; font-weight: 700; color: var(--surface-heading); }
.mc-detail__count { margin: 0; font-size: var(--text-sm); color: var(--surface-text); }

.mc-list { list-style: none; padding: 0; margin: 0; }
.mc-list--cols { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px 32px; }
.mc-list--card { border: 1px solid var(--surface-3); border-radius: var(--radius-lg); background: var(--surface-1); }
.mc-hit { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 4px 24px; padding: 16px; border-top: 1px solid var(--surface-3); }
.mc-hit:first-child { border-top: none; }
.mc-hit__date { margin: 0; font-weight: 600; color: var(--surface-heading); }
.mc-hit__body { display: flex; flex-direction: column; gap: 4px; align-items: flex-start; min-width: 0; }
.mc-hit__show { font-size: var(--text-sm); }

/* Phones: seven columns won't fit a name, so a list of the days that have dates */
@media (max-width: 720px) {
  .mc-bar__nav { width: 100%; }
  .mc-bar__nav :deep(.mc-bar__month) { flex: 1; width: auto; min-width: 0; }
  .mc-bar__filter, .mc-bar__select, .mc-search { width: 100%; }
  .mc-hit { grid-template-columns: minmax(0, 1fr); }
  .mc-weekdays, .mc-cell--blank, .mc-cell--none { display: none; }
  .mc-grid { grid-template-columns: minmax(0, 1fr); }
  .mc-grid:not(:has(.mc-day__events)) { display: none; }
  .mc-cell { min-height: 0; }
  .mc-day { padding: 12px; }
  .mc-day :deep(.mc-day__num) { display: none; }
  .mc-day :deep(.mc-day__full) { position: static; width: auto; height: auto; clip-path: none; white-space: normal; color: var(--surface-heading); font-weight: 700; }
  .mc-ev__name { display: block; }
}
</style>
