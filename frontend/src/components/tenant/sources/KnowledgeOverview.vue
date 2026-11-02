<template>
  <div class="ko">
    <!-- The dates the chatbot can answer in the next two weeks -->
    <section class="ko-strip" :aria-label="$t('knowledge.overview.stripTitle')">
      <div class="ko-strip__head">
        <CardTitle as="h2">{{ $t('knowledge.overview.stripTitle') }}</CardTitle>
        <CardDescription>{{ $t('knowledge.overview.stripSub') }}</CardDescription>
      </div>

      <ol v-if="loading && !data" class="ko-days" aria-busy="true">
        <li v-for="n in 14" :key="n" class="ko-day">
          <Skeleton class="ghost--line" style="width: 28px; height: 10px" />
          <Skeleton style="width: 36px; height: 24px; margin: 6px 0 10px" />
          <Skeleton v-if="n % 3 === 1" style="height: 34px" />
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
          <Switch id="ko-cal" :model-value="calendarsOn" :disabled="savingCal" @update:model-value="setCalendars" />
        </div>
        <p v-if="tenant?.test_protected && calendarsOn" class="meta ko-cal__warn">{{ $t('knowledge.calendars.protected') }}</p>
        <template v-else-if="calendarsOn && feeds.length">
          <button type="button" class="ko-cal__more" :aria-expanded="showFeeds" @click="showFeeds = !showFeeds">
            {{ $t('knowledge.calendars.count', { n: feeds.length }, feeds.length) }}
            <span class="ko-cal__more-action">{{ showFeeds ? $t('knowledge.calendars.hide') : $t('knowledge.calendars.show') }}</span>
          </button>
          <ul v-if="showFeeds" class="ko-cal__list">
            <li v-for="f in feeds" :key="f.key" class="ko-cal__feed">
              <span class="ko-cal__name">{{ f.zone ? `${f.series} (${f.zone})` : f.series }}</span>
              <span class="meta">{{ $t('knowledge.calendars.dates', { n: f.count }, f.count) }}</span>
              <button type="button" class="ko-cal__copy" :title="$t('knowledge.calendars.copy')" :aria-label="`${$t('knowledge.calendars.copy')}: ${f.series}`" @click="copyFeed(f)">
                <font-awesome-icon :icon="['fas', copied === f.key ? 'check' : 'link']" />
              </button>
            </li>
          </ul>
        </template>
      </div>
    </section>

    <!-- What the chatbot knows about reaching the organisation, read from the website footer -->
    <BcPanel as="section"  v-if="contact" class="ko-contact" :aria-label="$t('knowledge.contact.title')" :title="$t('knowledge.contact.title')" :description="$t('knowledge.contact.sub')">
      <div class="ko-contact__grid">
        <div class="ko-contact__col">
          <p v-if="contact.name" class="ko-contact__name">{{ contact.name }}</p>
          <a v-if="contactAddress && contact.maps_url" :href="contact.maps_url" target="_blank" rel="noopener noreferrer" class="ko-contact__line">{{ contactAddress }}</a>
          <p v-else-if="contactAddress" class="ko-contact__line">{{ contactAddress }}</p>
          <p v-if="contact.phone" class="ko-contact__line">{{ contact.phone }}</p>
          <p v-if="contact.email" class="ko-contact__line">{{ contact.email }}</p>
        </div>
        <dl v-if="contact.opening_hours?.length" class="ko-contact__hours">
          <template v-for="(h, i) in contact.opening_hours" :key="i">
            <dt>{{ h.days }}</dt>
            <dd>{{ h.hours }}</dd>
          </template>
        </dl>
      </div>
      <p v-if="contact.hours_note" class="meta">{{ contact.hours_note }}</p>
    </BcPanel>

  </div>
</template>

<script setup>
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { CardDescription, CardTitle } from '@/components/ui/card';
import { BcPanel } from '@/components/ui';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useTenantsStore } from '@/stores/tenants';
import { useToast } from '@/composables/useToast';

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


// ── Calendar feeds ──────────────────────────────────────────────────
const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const tenant = computed(() => tenantsStore.currentTenant);
const calendarsOn = computed(() => tenant.value?.calendar_feeds !== false);
const feeds = ref([]);
const savingCal = ref(false);
const copied = ref(null);
const showFeeds = ref(false);

// read from the website footer on each crawl
const contact = computed(() => tenant.value?.contact_card || null);
const contactAddress = computed(() => {
  const c = contact.value || {};
  return [c.street, [c.postal_code, c.city].filter(Boolean).join(' ')].filter(Boolean).join(', ');
});

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
.ko-strip__head { margin-bottom: 16px; }
.ko-strip__empty { font-size: 16px; color: var(--surface-muted); max-width: var(--measure); }

/* Two weeks as two rows of seven days — the shape of a printed collection calendar */
.ko-days {
  list-style: none; padding: 0;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  border-top: 1px solid var(--surface-3);
}
.ko-day {
  min-height: 118px;
  padding: 12px 12px 16px;
  border-left: 1px solid var(--surface-3);
  border-bottom: 1px solid var(--surface-3);
  position: relative;
  min-width: 0;
}
.ko-day:nth-child(7n + 1) { border-left: none; }
.ko-day:nth-last-child(-n + 7) { border-bottom: none; }
.ko-day--weekend { background: var(--surface-0); }
.ko-day--today::before {
  content: ''; position: absolute; left: 0; right: 0; top: -1px; height: 3px;
  background: var(--interactive);
}
.ko-day__weekday { font-size: var(--text-xs); font-weight: 600; color: var(--surface-muted); }
.ko-day--today .ko-day__weekday { color: var(--interactive); }
.ko-day__date { display: flex; align-items: baseline; gap: 4px; margin: 2px 0 8px; }
.ko-day__num { font-size: 28px; font-weight: 700; line-height: 1; color: var(--text-primary); letter-spacing: -0.01em; }
.ko-day--empty .ko-day__num { color: var(--text-disabled); }
.ko-day__month { font-size: var(--text-xs); color: var(--surface-muted); }

.ko-day__events { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.ko-event {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 8px;
  border-radius: var(--radius-sm);
  background: var(--interactive-soft);
}
.ko-event--moved { background: var(--status-warning-soft); border-left-color: var(--status-warning); }
.ko-event__series { font-size: 14px; font-weight: 700; color: var(--surface-heading); line-height: 1.25; hyphens: auto; overflow-wrap: break-word; }
.ko-event__zone { font-size: var(--text-xs); color: var(--surface-text); }
.ko-event__moved { font-size: var(--text-xs); font-weight: 700; color: var(--status-warning); }

/* ── Calendars ───────────────────────────────────────────────────── */
.ko-cal { margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--surface-3); }
.ko-cal__row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.ko-cal__title { font-size: 16px; font-weight: 700; color: var(--surface-heading); cursor: pointer; }
.ko-cal__warn { margin-top: 8px; color: var(--status-warning); }
.ko-cal__list { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; max-width: 560px; }
.ko-cal__feed { display: grid; grid-template-columns: minmax(0, 1fr) auto 32px; align-items: center; gap: 12px; padding: 8px 0; border-top: 1px solid var(--surface-3); font-size: var(--text-sm); }
.ko-cal__feed:first-child { border-top: none; }
.ko-cal__name { font-size: var(--text-sm); font-weight: 700; color: var(--surface-heading); }
.ko-cal__copy { width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; border: none; border-radius: var(--radius-md); background: none; color: var(--surface-muted); cursor: pointer; }
.ko-cal__copy:hover { color: var(--interactive); background: var(--surface-3); }
.ko-cal__more { margin-top: 8px; background: none; border: none; padding: 0; cursor: pointer; font-size: var(--text-sm); color: var(--surface-text); }
.ko-cal__more-action { margin-left: 8px; font-weight: 600; color: var(--interactive); }
.ko-cal__more:hover .ko-cal__more-action { text-decoration: underline; }

/* ── Needs you ───────────────────────────────────────────────────── */

/* Phones: one day per row, empty days collapse to a single line */
@media (max-width: 760px) {
  .ko-strip { padding: 16px 16px 16px; }
  .ko-days { grid-template-columns: 1fr; }
  .ko-day { min-height: 0; display: grid; grid-template-columns: 64px 1fr; gap: 4px 12px; border-left: none; padding: 8px 0; }
  .ko-day:nth-last-child(-n + 7) { border-bottom: 1px solid var(--surface-3); }
  .ko-day:last-child { border-bottom: none; }
  .ko-day__weekday { grid-column: 1; }
  .ko-day__date { grid-column: 1; margin: 0; }
  .ko-day__events { grid-column: 2; grid-row: 1 / span 2; }
  .ko-day__num { font-size: var(--text-lg); }
  .ko-day--today::before { right: auto; bottom: 0; width: 3px; height: auto; left: -16px; }
}
.ko-contact { margin-top: 16px; }
.ko-contact__grid { display: flex; flex-wrap: wrap; gap: 16px 48px; margin-top: 16px; }
.ko-contact__col { display: flex; flex-direction: column; gap: 4px; font-size: var(--text-sm); color: var(--surface-text); }
.ko-contact__name { font-weight: 700; color: var(--surface-heading); }
a.ko-contact__line { color: var(--interactive); text-decoration: none; }
a.ko-contact__line:hover { text-decoration: underline; }
.ko-contact__hours { display: grid; grid-template-columns: auto auto; gap: 4px 20px; margin: 0; font-size: var(--text-sm); }
.ko-contact__hours dt { color: var(--surface-muted); }
.ko-contact__hours dd { margin: 0; color: var(--surface-heading); font-variant-numeric: tabular-nums; }
</style>
