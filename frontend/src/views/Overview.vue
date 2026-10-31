<template>
  <div class="ov">
    <BcPageHeader :title="$t('pages.overviewTitle')" :lede="$t('pages.overview')">
      <template v-if="data" #status><BcStatusBadge :status="!data.is_active ? 'off' : data.widget_enabled ? 'on' : 'hidden'" /></template>
      <template #actions>
        <BcSegmentedControl v-model="days" :options="PERIODS" size="sm" :label="$t('overview.period')" />
      </template>
    </BcPageHeader>

    <template v-if="!data && loading">
      <BcPanel><BcSkeleton :lines="2" /></BcPanel>
      <BcPanel>
        <div class="ov-figures"><BcSkeleton v-for="n in 4" :key="n" variant="figure" /></div>
      </BcPanel>
    </template>
    <BcNotice v-else-if="!data" tone="error" :title="$t('overview.loadFailed')">
      <template #actions><BcButton size="sm" variant="secondary" @click="load">{{ $t('common.retry') }}</BcButton></template>
    </BcNotice>

    <template v-else>
      <!-- On / off: the one thing that has to be unmistakable -->
      <BcPanel>
        <BcSwitch :model-value="data.is_active" :disabled="switching" :state-text="false"
          :label="data.is_active ? $t('overview.status.onTitle') : $t('overview.status.offTitle')"
          :description="data.is_active ? (data.widget_enabled ? $t('overview.status.onBody') : $t('overview.status.onHidden')) : $t('overview.status.offBody')"
          @update:model-value="(on) => (on ? setActive(true) : (askOff = true))" />
      </BcPanel>

      <!-- Usage and money in the period -->
      <BcSection :title="$t('overview.usage.title', { n: data.days })">
        <template #actions>
          <router-link :to="{ name: 'TenantInsights', params: { tenantId } }" class="bc-btn bc-btn--quiet bc-btn--sm">{{ $t('overview.usage.more') }}</router-link>
        </template>
        <BcPanel>
          <div class="ov-figures">
            <BcKeyFigure :label="$t('overview.usage.conversations')" :value="formatNumber(data.usage.conversations)"
              :delta="trend(data.usage.conversations, data.usage.conversations_prev)" :hint="isNew(data.usage.conversations, data.usage.conversations_prev) ? $t('overview.usage.new') : ''" />
            <BcKeyFigure :label="$t('overview.usage.questions')" :value="formatNumber(data.usage.questions)"
              :delta="trend(data.usage.questions, data.usage.questions_prev)" :hint="isNew(data.usage.questions, data.usage.questions_prev) ? $t('overview.usage.new') : ''" />
            <BcKeyFigure :label="$t('overview.usage.spent')" :value="formatCHF(data.costs.chat_chf + data.costs.learning_chf + (data.costs.review_chf || 0))"
              :hint="$t('overview.usage.spentSplit3', { chat: formatNumber(data.costs.chat_chf, 2), learning: formatNumber(data.costs.learning_chf, 2), reviews: formatNumber(data.costs.review_chf || 0, 2) })" />
            <BcKeyFigure :label="$t('overview.usage.balance')">
              <template #value><BcMoney :amount="data.costs.balance_chf" size="figure" :tone="data.costs.balance_chf < 5 ? 'warn' : ''" /></template>
              <template #action>
                <router-link :to="{ name: 'AccountSettings', params: { section: 'billing' } }" class="ov-topup">{{ $t('overview.usage.topUp') }}</router-link>
              </template>
            </BcKeyFigure>
          </div>

          <!-- Questions per day -->
          <figure class="bc-chart ov-chart">
            <svg class="bc-chart__svg" :viewBox="`0 0 ${chart.w} ${chart.h}`" preserveAspectRatio="none" role="img" :height="chart.h"
              :aria-label="$t('overview.usage.chartLabel', { n: data.usage.questions, days: data.days })">
              <line class="bc-chart__base" x1="0" :x2="chart.w" :y1="chart.h - 0.5" :y2="chart.h - 0.5" />
              <rect v-for="(b, i) in chart.bars" :key="i" :x="b.x" :y="b.y" :width="b.w" :height="b.h" rx="1.5" class="bc-chart__bar--1">
                <title>{{ b.label }}</title>
              </rect>
            </svg>
            <figcaption class="ov-chart__axis">
              <span>{{ fmtDay(data.usage.series[0]?.date) }}</span>
              <span>{{ $t('overview.usage.today') }}</span>
            </figcaption>
          </figure>
        </BcPanel>
      </BcSection>

      <div class="ov-grid">
        <!-- Knowledge -->
        <BcPanel :title="$t('overview.knowledge.title')">
          <template #actions>
            <router-link :to="{ name: 'TenantSources', params: { tenantId } }" class="bc-btn bc-btn--quiet bc-btn--sm">{{ $t('overview.knowledge.more') }}</router-link>
          </template>
          <div class="ov-facts">
            <BcKeyFigure size="sm" :label="$t('overview.knowledge.pages')" :value="formatNumber(data.knowledge.pages)" />
            <BcKeyFigure size="sm" :label="$t('overview.knowledge.files')" :value="formatNumber(data.knowledge.files)" />
            <BcKeyFigure size="sm" :label="$t('overview.knowledge.sections')" :value="formatNumber(data.knowledge.sections)" />
            <BcKeyFigure size="sm" :label="$t('overview.knowledge.upcoming')" :value="formatNumber(data.knowledge.upcoming_dates)" />
          </div>
          <div class="ov-crawl">
            <p class="ov-crawl__label">{{ $t('overview.knowledge.lastCrawl') }}</p>
            <template v-if="data.last_crawl">
              <div class="ov-crawl__row">
                <router-link :to="{ name: 'TenantCrawl', params: { tenantId, jobId: data.last_crawl.id } }" class="ov-crawl__url">{{ displayUrl(data.last_crawl.start_url) }}</router-link>
                <BcStatusBadge :status="CRAWL_STATUS[data.last_crawl.status] || 'stopped'" size="sm" />
              </div>
              <p class="ov-muted">
                {{ fmtDateTime(data.last_crawl.finished_at || data.last_crawl.created_at) }}<template v-if="data.last_crawl.counts"> · {{ $t('overview.knowledge.crawlCounts', { learned: data.last_crawl.counts.learned || 0, unchanged: data.last_crawl.counts.unchanged || 0 }) }}</template>
              </p>
            </template>
            <p v-else class="ov-muted">{{ $t('overview.knowledge.noCrawl') }}</p>
          </div>
        </BcPanel>

        <!-- Latest questions -->
        <BcPanel :title="$t('overview.latest.title')">
          <template #actions>
            <router-link :to="{ name: 'TenantInsights', params: { tenantId } }" class="bc-btn bc-btn--quiet bc-btn--sm">{{ $t('overview.latest.more') }}</router-link>
          </template>
          <BcNotice v-if="data.usage.open_findings" tone="warning" :title="$t('overview.latest.findings', { n: data.usage.open_findings })">
            <template #actions>
              <router-link :to="{ name: 'TenantInsights', params: { tenantId } }" class="bc-btn bc-btn--secondary bc-btn--sm">{{ $t('overview.usage.more') }}</router-link>
            </template>
          </BcNotice>
          <ol v-if="data.usage.latest.length" class="ov-questions">
            <li v-for="(q, i) in data.usage.latest" :key="i">
              <p>{{ q.question }}</p>
              <time class="ov-muted" :datetime="q.at">{{ fmtDateTime(q.at) }}</time>
            </li>
          </ol>
          <BcEmptyState v-else compact icon="comments" :title="$t('overview.latest.none')" />
        </BcPanel>
      </div>
    </template>

    <ConfirmationModal
      :show="askOff"
      :title="$t('overview.status.confirmTitle')"
      :message="$t('overview.status.confirmBody')"
      :confirm-button-text="$t('overview.status.switchOff')"
      @confirm="setActive(false)"
      @cancel="askOff = false"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useToast } from '@/composables/useToast';
import { useTenantsStore } from '@/stores/tenants';
import { useCrawlText } from '@/composables/useCrawl';
import ConfirmationModal from '@/components/ConfirmationModal.vue';
import {
  BcButton, BcEmptyState, BcKeyFigure, BcMoney, BcNotice, BcPageHeader, BcPanel, BcSection, BcSegmentedControl,
  BcSkeleton, BcStatusBadge, BcSwitch,
} from '@/components/ui';
import { formatCHF, formatNumber } from '@/utils/format';

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

const PERIODS = computed(() => [7, 30, 90].map((d) => ({ value: d, label: t('overview.days', { n: d }) })));
// a crawl's status in the design system's badge names
const CRAWL_STATUS = { IN_PROGRESS: 'scanning', SCANNED: 'ready', INDEXING: 'learning', COMPLETED: 'done', FAILED: 'stopped' };
const fmtDay = (iso) => (iso ? new Date(`${iso}T00:00:00`).toLocaleDateString(locale.value, { day: 'numeric', month: 'short' }) : '');

// Bars for questions per day; height relative to the busiest day
const chart = computed(() => {
  const series = data.value?.usage.series || [];
  const w = 600, h = 96, gap = series.length > 60 ? 1 : 3;
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

// Change against the previous period of the same length, in percent
const trend = (now, before) => (before ? Math.round(((now - before) / before) * 100) : null);
const isNew = (now, before) => !before && now > 0;
</script>

<style scoped>
.ov { display: flex; flex-direction: column; gap: var(--space-8); }
.ov-figures { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-6); }
.ov-topup { font-size: 14px; font-weight: 600; }
.ov-chart { margin-top: var(--space-8); }
.ov-chart__axis { display: flex; justify-content: space-between; font-size: 13px; line-height: 16px; color: var(--text-tertiary); }
.ov-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-6); align-items: start; }
.ov-facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-5) var(--space-6); }
.ov-crawl { margin-top: var(--space-6); padding-top: var(--space-5); border-top: 1px solid var(--border-subtle); }
.ov-crawl__label { font-size: 14px; line-height: 20px; font-weight: 600; color: var(--text-secondary); margin-bottom: var(--space-2); }
.ov-crawl__row { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
.ov-crawl__url { font-weight: 600; }
.ov-muted { color: var(--text-secondary); font-size: 14px; line-height: 20px; }
.ov-questions { list-style: none; margin: var(--space-4) 0 0; padding: 0; }
.ov-questions li { padding: var(--space-3) 0; border-top: 1px solid var(--border-subtle); }
.ov-questions li:first-child { border-top: none; padding-top: 0; }

@media (max-width: 1000px) {
  .ov-figures { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ov-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
