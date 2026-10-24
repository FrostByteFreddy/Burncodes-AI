<template>
  <div class="ov">
    <div class="page-head">
      <div>
        <h1 class="page-title">{{ $t('pages.overviewTitle') }}</h1>
        <p class="page-lede">{{ $t('pages.overview') }}</p>
      </div>
      <div class="ov-period" role="group" :aria-label="$t('overview.period')">
        <button v-for="d in [7, 30, 90]" :key="d" type="button" class="ov-period__btn" :class="{ 'ov-period__btn--on': days === d }" :aria-pressed="days === d" @click="days = d">
          {{ $t('overview.days', { n: d }) }}
        </button>
      </div>
    </div>

    <div v-if="!data && loading" class="ov-skeleton"></div>
    <p v-else-if="!data" class="meta">{{ $t('overview.loadFailed') }}</p>

    <template v-else>
      <!-- On / off: the one thing that has to be unmistakable -->
      <section class="ov-status" :class="data.is_active ? 'ov-status--on' : 'ov-status--off'">
        <span class="ov-status__dot" aria-hidden="true"></span>
        <div class="ov-status__text">
          <h2>{{ data.is_active ? $t('overview.status.onTitle') : $t('overview.status.offTitle') }}</h2>
          <p>{{ data.is_active ? (data.widget_enabled ? $t('overview.status.onBody') : $t('overview.status.onHidden')) : $t('overview.status.offBody') }}</p>
        </div>
        <button v-if="data.is_active" type="button" class="btn-quiet ov-status__off" :disabled="switching" @click="askOff = true">
          <font-awesome-icon :icon="['fas', 'power-off']" /> {{ $t('overview.status.switchOff') }}
        </button>
        <button v-else type="button" class="btn-action" :disabled="switching" @click="setActive(true)">
          <font-awesome-icon :icon="switching ? ['fas', 'spinner'] : ['fas', 'power-off']" :class="{ 'animate-spin': switching }" /> {{ $t('overview.status.switchOn') }}
        </button>
      </section>

      <!-- Usage and money in the period -->
      <section class="panel">
        <div class="ov-panel-head">
          <h2 class="panel-title">{{ $t('overview.usage.title', { n: data.days }) }}</h2>
          <router-link :to="{ name: 'TenantInsights', params: { tenantId } }" class="ov-link">{{ $t('overview.usage.more') }}</router-link>
        </div>
        <dl class="ov-figures">
          <div>
            <dt>{{ $t('overview.usage.conversations') }}</dt>
            <dd>{{ fmtInt(data.usage.conversations) }} <Trend :now="data.usage.conversations" :before="data.usage.conversations_prev" /></dd>
          </div>
          <div>
            <dt>{{ $t('overview.usage.questions') }}</dt>
            <dd>{{ fmtInt(data.usage.questions) }} <Trend :now="data.usage.questions" :before="data.usage.questions_prev" /></dd>
          </div>
          <div>
            <dt>{{ $t('overview.usage.spent') }}</dt>
            <dd>CHF {{ fmtChf(data.costs.chat_chf + data.costs.learning_chf) }}</dd>
            <p class="ov-split">{{ $t('overview.usage.spentSplit', { chat: fmtChf(data.costs.chat_chf), learning: fmtChf(data.costs.learning_chf) }) }}</p>
          </div>
          <div>
            <dt>{{ $t('overview.usage.balance') }}</dt>
            <dd :class="{ 'ov-low': data.costs.balance_chf < 5 }">CHF {{ fmtChf(data.costs.balance_chf) }}</dd>
            <router-link :to="{ name: 'Subscription' }" class="ov-split ov-link">{{ $t('overview.usage.topUp') }}</router-link>
          </div>
        </dl>

        <!-- Questions per day -->
        <figure class="ov-chart">
          <svg :viewBox="`0 0 ${chart.w} ${chart.h}`" preserveAspectRatio="none" role="img" :aria-label="$t('overview.usage.chartLabel', { n: data.usage.questions, days: data.days })">
            <rect v-for="(b, i) in chart.bars" :key="i" :x="b.x" :y="b.y" :width="b.w" :height="b.h" rx="1.5" class="ov-chart__bar" :class="{ 'ov-chart__bar--today': i === chart.bars.length - 1 }">
              <title>{{ b.label }}</title>
            </rect>
          </svg>
          <figcaption class="ov-chart__axis">
            <span>{{ fmtDay(data.usage.series[0]?.date) }}</span>
            <span>{{ $t('overview.usage.today') }}</span>
          </figcaption>
        </figure>
      </section>

      <div class="ov-grid">
        <!-- Knowledge -->
        <section class="panel">
          <div class="ov-panel-head">
            <h2 class="panel-title">{{ $t('overview.knowledge.title') }}</h2>
            <router-link :to="{ name: 'TenantSources', params: { tenantId } }" class="ov-link">{{ $t('overview.knowledge.more') }}</router-link>
          </div>
          <ul class="ov-facts">
            <li><strong>{{ fmtInt(data.knowledge.pages) }}</strong> {{ $t('overview.knowledge.pages') }}</li>
            <li><strong>{{ fmtInt(data.knowledge.files) }}</strong> {{ $t('overview.knowledge.files') }}</li>
            <li><strong>{{ fmtInt(data.knowledge.sections) }}</strong> {{ $t('overview.knowledge.sections') }}</li>
            <li><strong>{{ fmtInt(data.knowledge.upcoming_dates) }}</strong> {{ $t('overview.knowledge.upcoming') }}</li>
          </ul>
          <p v-if="data.knowledge.needs_attention" class="ov-attention">
            <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
            <router-link :to="{ name: 'TenantSources', params: { tenantId } }">{{ $t('overview.knowledge.attention', { n: data.knowledge.needs_attention }) }}</router-link>
          </p>

          <div class="ov-crawl">
            <h3>{{ $t('overview.knowledge.lastCrawl') }}</h3>
            <template v-if="data.last_crawl">
              <router-link :to="{ name: 'TenantCrawl', params: { tenantId, jobId: data.last_crawl.id } }" class="ov-crawl__url">{{ displayUrl(data.last_crawl.start_url) }}</router-link>
              <p class="meta">
                {{ $t(`knowledge.status.${data.last_crawl.status}`) }}, {{ fmtDateTime(data.last_crawl.finished_at || data.last_crawl.created_at) }}<template v-if="data.last_crawl.counts">. {{ $t('overview.knowledge.crawlCounts', { learned: data.last_crawl.counts.learned || 0, unchanged: data.last_crawl.counts.unchanged || 0 }) }}</template>
              </p>
            </template>
            <p v-else class="meta">{{ $t('overview.knowledge.noCrawl') }}</p>
          </div>
        </section>

        <!-- Latest questions -->
        <section class="panel">
          <div class="ov-panel-head">
            <h2 class="panel-title">{{ $t('overview.latest.title') }}</h2>
            <router-link :to="{ name: 'TenantInsights', params: { tenantId } }" class="ov-link">{{ $t('overview.latest.more') }}</router-link>
          </div>
          <p v-if="data.usage.open_findings" class="ov-attention ov-attention--top">
            <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
            <router-link :to="{ name: 'TenantInsights', params: { tenantId } }">{{ $t('overview.latest.findings', { n: data.usage.open_findings }) }}</router-link>
          </p>
          <ol v-if="data.usage.latest.length" class="ov-questions">
            <li v-for="(q, i) in data.usage.latest" :key="i">
              <p>{{ q.question }}</p>
              <time class="meta" :datetime="q.at">{{ fmtDateTime(q.at) }}</time>
            </li>
          </ol>
          <p v-else class="meta">{{ $t('overview.latest.none') }}</p>
        </section>
      </div>

      <!-- Everything that runs on a schedule, in one place -->
      <section id="automation" class="panel">
        <h2 class="panel-title">{{ $t('overview.auto.title') }}</h2>
        <p class="panel-sub">{{ $t('overview.auto.sub') }}</p>
        <ul class="ov-auto">
          <li class="ov-auto__row">
            <div class="ov-auto__text">
              <label for="auto-recrawl" class="ov-auto__name">{{ $t('overview.auto.recrawl') }}</label>
              <p class="meta">{{ $t('overview.auto.recrawlHow') }}</p>
              <p class="ov-auto__when">{{ when(data.automation.recrawl) }}</p>
            </div>
            <select id="auto-recrawl" class="ov-auto__select" :value="recrawlValue" :disabled="savingAuto || !data.automation.recrawl.has_websites" @change="saveRecrawl($event.target.value)">
              <option value="off">{{ $t('overview.auto.off') }}</option>
              <option v-for="n in [7, 14, 30]" :key="n" :value="String(n)">{{ $t(`knowledge.recrawl.every${n}`) }}</option>
            </select>
          </li>
          <li class="ov-auto__row">
            <div class="ov-auto__text">
              <label for="auto-review" class="ov-auto__name">{{ $t('overview.auto.review') }}</label>
              <p class="meta">{{ $t('overview.auto.reviewHow', { cost: fmtChf(data.automation.review.est_chf_per_conversation) }) }}</p>
              <p class="ov-auto__when">{{ when(data.automation.review) }}</p>
            </div>
            <select id="auto-review" class="ov-auto__select" :value="reviewValue" :disabled="savingAuto" @change="saveReview($event.target.value)">
              <option value="off">{{ $t('overview.auto.off') }}</option>
              <option value="1">{{ $t('overview.auto.daily') }}</option>
              <option value="7">{{ $t('overview.auto.weekly') }}</option>
            </select>
          </li>
        </ul>
      </section>
    </template>

    <ConfirmationModal
      :show="askOff"
      :title="$t('overview.status.confirmTitle')"
      :message="$t('overview.status.confirmBody')"
      :confirmButtonText="$t('overview.status.switchOff')"
      @confirm="setActive(false)"
      @cancel="askOff = false"
    />
  </div>
</template>

<script setup>
import { computed, h, nextTick, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useToast } from '@/composables/useToast';
import { useTenantsStore } from '@/stores/tenants';
import { useCrawlText } from '@/composables/useCrawl';
import ConfirmationModal from '@/components/ConfirmationModal.vue';

const { t, locale } = useI18n();
const { addToast } = useToast();
const tenantsStore = useTenantsStore();
const { fmtDateTime, displayUrl } = useCrawlText();

const tenantId = computed(() => tenantsStore.currentTenant?.id || '');
const days = ref(30);
const data = ref(null);
const loading = ref(false);
const switching = ref(false);
const askOff = ref(false);

const load = async () => {
  if (!tenantId.value) return;
  loading.value = true;
  try {
    data.value = (await apiClient.get(`/tenants/${tenantId.value}/overview`, { params: { days: days.value } })).data;
  } catch { data.value = null; }
  finally { loading.value = false; }
};
watch([tenantId, days], load, { immediate: true });

// Links from Knowledge and Insights point at the scheduled tasks panel
watch(data, async (d, before) => {
  if (!d || before || window.location.hash !== '#automation') return;
  await nextTick();
  document.getElementById('automation')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

const setActive = async (on) => {
  askOff.value = false;
  switching.value = true;
  try {
    await apiClient.put(`/tenants/${tenantId.value}`, { is_active: on });
    data.value = { ...data.value, is_active: on };
    addToast(on ? t('overview.status.switchedOn') : t('overview.status.switchedOff'), 'success');
    tenantsStore.refetch?.(tenantId.value);
  } catch {
    addToast(t('tenant.settings.actions.saveFailed'), 'error');
  } finally { switching.value = false; }
};

// ── Scheduled tasks ─────────────────────────────────────────────────
const savingAuto = ref(false);
const recrawlValue = computed(() => (data.value?.automation.recrawl.enabled ? String(data.value.automation.recrawl.interval_days) : 'off'));
const reviewValue = computed(() => (data.value?.automation.review.enabled ? String(data.value.automation.review.interval_days) : 'off'));
const saveAuto = async (payload) => {
  savingAuto.value = true;
  try {
    await apiClient.put(`/tenants/${tenantId.value}`, payload);
    await load();
    addToast(t('overview.auto.saved'), 'success');
  } catch { addToast(t('tenant.settings.actions.saveFailed'), 'error'); }
  finally { savingAuto.value = false; }
};
const saveRecrawl = (v) => saveAuto(v === 'off' ? { auto_recrawl: false } : { auto_recrawl: true, recrawl_interval_days: Number(v) });
const saveReview = (v) => saveAuto(v === 'off' ? { review_chats: false } : { review_chats: true, review_interval_days: Number(v) });
const when = (task) => {
  const parts = [task.last_run ? t('overview.auto.last', { date: fmtDateTime(task.last_run) }) : t('overview.auto.never')];
  if (task.next_run) parts.push(t('overview.auto.next', { date: fmtDateTime(task.next_run) }));
  return parts.join('. ') + '.';
};

const fmtInt = (n) => Number(n || 0).toLocaleString(locale.value);
const fmtChf = (n) => Number(n || 0).toFixed(2);
const fmtDay = (iso) => (iso ? new Date(`${iso}T00:00:00`).toLocaleDateString(locale.value, { day: 'numeric', month: 'short' }) : '');

// Bars for questions per day; height relative to the busiest day
const chart = computed(() => {
  const series = data.value?.usage.series || [];
  const w = 600, h = 72, gap = series.length > 60 ? 1 : 3;
  const bw = series.length ? (w - gap * (series.length - 1)) / series.length : 0;
  const max = Math.max(1, ...series.map((s) => s.questions));
  return {
    w, h,
    bars: series.map((s, i) => {
      const bh = s.questions ? Math.max(3, (s.questions / max) * (h - 4)) : 2;
      return { x: i * (bw + gap), y: h - bh, w: bw, h: bh, label: `${fmtDay(s.date)}: ${s.questions}` };
    }),
  };
});

// Change against the previous period of the same length
const Trend = (props) => {
  const { now, before } = props;
  if (!before && !now) return null;
  if (!before) return h('span', { class: 'ov-trend ov-trend--up' }, t('overview.usage.new'));
  const pct = Math.round(((now - before) / before) * 100);
  if (pct === 0) return h('span', { class: 'ov-trend' }, t('overview.usage.same'));
  return h('span', { class: ['ov-trend', pct > 0 ? 'ov-trend--up' : 'ov-trend--down'], title: t('overview.usage.vsPrevious') },
    `${pct > 0 ? '+' : ''}${pct}%`);
};
Trend.props = ['now', 'before'];
</script>

<style scoped>
.ov { display: flex; flex-direction: column; gap: 20px; }
.ov-skeleton { height: 360px; border-radius: var(--radius-xl); background: var(--surface-1); }

.ov-period { display: inline-flex; gap: 2px; padding: 3px; border-radius: var(--radius-pill); background: var(--surface-1); border: 1px solid var(--surface-3); }
.ov-period__btn { padding: 6px 14px; border: none; border-radius: var(--radius-pill); background: none; cursor: pointer; font: inherit; font-size: var(--text-sm); font-weight: 600; color: var(--surface-muted); }
.ov-period__btn:hover { color: var(--surface-heading); }
.ov-period__btn--on { background: var(--surface-3); color: var(--surface-heading); }

/* Status */
.ov-status {
  display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 16px;
  padding: 20px 24px; border-radius: var(--radius-xl); border: 1px solid var(--surface-3); background: var(--surface-1);
}
.ov-status--on { border-color: rgba(60, 203, 154, 0.35); }
.ov-status--off { border-color: rgba(255, 107, 107, 0.45); background: var(--status-error-soft, rgba(255, 107, 107, 0.08)); }
.ov-status__dot { width: 14px; height: 14px; border-radius: 50%; background: var(--status-success); box-shadow: 0 0 0 5px rgba(60, 203, 154, 0.18); }
.ov-status--off .ov-status__dot { background: var(--status-error); box-shadow: 0 0 0 5px rgba(255, 107, 107, 0.18); }
.ov-status__text h2 { font-size: var(--text-lg); font-weight: 700; color: var(--surface-heading); }
.ov-status__text p { margin-top: 2px; font-size: 15px; color: var(--surface-text); max-width: var(--measure); }
.ov-status__off:hover:not(:disabled) { border-color: var(--status-error); color: var(--status-error); }

.ov-panel-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.ov-link { font-size: var(--text-sm); font-weight: 600; color: var(--interactive); text-decoration: none; }
.ov-link:hover { text-decoration: underline; }

/* Figures */
.ov-figures { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px 24px; margin: 0; }
.ov-figures dt { font-size: var(--text-sm); color: var(--surface-muted); }
.ov-figures dd { margin: 2px 0 0; display: flex; align-items: baseline; gap: 8px; font-size: var(--text-2xl); font-weight: 800; color: var(--surface-heading); letter-spacing: -0.01em; }
.ov-split { display: block; margin-top: 2px; font-size: var(--text-xs); color: var(--surface-muted); }
.ov-low { color: var(--status-warning) !important; }
:deep(.ov-trend) { font-size: var(--text-xs); font-weight: 700; color: var(--surface-muted); letter-spacing: 0; }
:deep(.ov-trend--up) { color: var(--status-success); }
:deep(.ov-trend--down) { color: var(--status-warning); }

.ov-chart { margin: 20px 0 0; }
.ov-chart svg { display: block; width: 100%; height: 72px; }
.ov-chart__bar { fill: var(--surface-3); }
.ov-chart__bar:hover { fill: var(--interactive); }
.ov-chart__bar--today { fill: var(--interactive-strong); }
.ov-chart__axis { display: flex; justify-content: space-between; margin-top: 6px; font-size: var(--text-xs); color: var(--surface-muted); }

.ov-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; align-items: start; }

/* Knowledge */
.ov-facts { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 20px; font-size: 15px; color: var(--surface-muted); }
.ov-facts strong { font-size: var(--text-lg); color: var(--surface-heading); margin-right: 4px; }
.ov-attention { display: flex; gap: 8px; align-items: baseline; margin-top: 14px; font-size: var(--text-sm); color: var(--status-warning); }
.ov-attention a { color: inherit; font-weight: 600; }
.ov-attention--top { margin: -4px 0 12px; }
.ov-crawl { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--surface-3); display: flex; flex-direction: column; gap: 4px; }
.ov-crawl h3 { font-size: var(--text-sm); font-weight: 700; color: var(--surface-heading); }
.ov-crawl__url { font-size: 15px; font-weight: 600; color: var(--surface-heading); text-decoration: none; overflow-wrap: anywhere; }
.ov-crawl__url:hover { color: var(--interactive); text-decoration: underline; }

/* Scheduled tasks */
.ov-auto { list-style: none; padding: 0; margin: 16px 0 0; display: flex; flex-direction: column; }
.ov-auto__row { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 14px 0; border-top: 1px solid var(--surface-3); }
.ov-auto__row:first-child { border-top: none; padding-top: 0; }
.ov-auto__text { min-width: 0; display: flex; flex-direction: column; gap: 2px; max-width: var(--measure); }
.ov-auto__name { font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.ov-auto__when { font-size: var(--text-xs); color: var(--surface-muted); }
.ov-auto__select {
  flex-shrink: 0; min-width: 170px; padding: 8px 32px 8px 12px; border-radius: var(--radius-md);
  background-color: var(--surface-2); border: 1px solid var(--surface-3);
  color: var(--surface-heading); font: inherit; font-size: var(--text-sm); cursor: pointer;
}
.ov-auto__select:hover:not(:disabled) { border-color: var(--surface-muted); }
.ov-auto__select:disabled { opacity: 0.5; cursor: not-allowed; }

/* Latest questions */
.ov-questions { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; }
.ov-questions li { padding: 10px 0; border-top: 1px solid var(--surface-3); }
.ov-questions li:first-child { border-top: none; padding-top: 0; }
.ov-questions p { font-size: 15px; color: var(--surface-heading); overflow-wrap: anywhere; }

@media (max-width: 900px) {
  .ov-figures { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ov-grid { grid-template-columns: minmax(0, 1fr); }
  .ov-status { grid-template-columns: auto minmax(0, 1fr); }
  .ov-status > button { grid-column: 1 / -1; justify-self: start; }
  .ov-auto__row { flex-direction: column; align-items: stretch; }
}
</style>
