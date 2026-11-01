<template>
  <div class="crawl-page">
    <template v-if="!job && loading">
      <BcSkeleton :lines="2" />
      <BcPanel><BcSkeleton :lines="4" /></BcPanel>
    </template>
    <BcNotice v-else-if="!job" tone="error" :title="$t('knowledge.job.actionFailed')">
      <template #actions><BcButton size="sm" variant="secondary" @click="fetchJob">{{ $t('common.retry') }}</BcButton></template>
    </BcNotice>

    <template v-else>
      <BcPageHeader :title="displayUrl(job.start_url)"
        :lede="(job.trigger === 'scheduled' ? $t('knowledge.job.scheduled', { date: fmtDateTime(job.created_at) }) : $t('knowledge.job.started', { date: fmtDateTime(job.created_at) })) + (job.single_page_only ? ` · ${$t('knowledge.job.singlePage')}` : '')">
        <template #eyebrow>
          <router-link :to="{ name: 'TenantSources', params: { tenantId } }">{{ $t('pages.knowledgeTitle') }}</router-link> › {{ $t('knowledge.crawls.title') }}
        </template>
        <template #status><BcStatusBadge :status="badge" /></template>
        <template #actions>
          <a :href="job.start_url" target="_blank" rel="noopener noreferrer" class="bc-btn bc-btn--quiet bc-btn--md">
            <BcIcon name="arrow-up-right-from-square" />{{ $t('knowledge.job.openSite') }}
          </a>
          <BcButton v-if="job.status === 'IN_PROGRESS' || job.status === 'INDEXING'" variant="secondary" icon="stop" :disabled="busy" @click="onStop">{{ $t('knowledge.job.stop') }}</BcButton>
          <BcButton v-if="job.status === 'FAILED'" variant="primary" icon="play" :loading="busy" @click="onResume">{{ $t('knowledge.job.resume') }}</BcButton>
          <BcButton v-if="!isActive" variant="destructive-quiet" icon="trash" @click="askDelete = true">{{ $t('knowledge.job.delete') }}</BcButton>
        </template>
      </BcPageHeader>

      <!-- Scan finished: what learning will do and cost -->
      <BcNotice v-if="isPreparing(job)" tone="info" icon="spinner" :title="$t('knowledge.estimate.preparing')" />
      <section v-else-if="job.status === 'SCANNED'" class="crawl-estimate">
        <BcPanel>
          <div class="crawl-estimate__grid">
            <div class="crawl-estimate__text">
              <h2 class="crawl-estimate__title">
                {{ estimate.to_learn ? $t('onboarding.learning.estimateTitle', { n: formatNumber(estimate.to_learn) }, estimate.to_learn) : $t('knowledge.estimate.title') }}
              </h2>
              <p class="crawl-muted">
                {{ estimate.to_learn ? $t('knowledge.estimate.body', { n: formatNumber(estimate.to_learn) }) : $t(estimate.skipped ? 'knowledge.estimate.noneSelected' : 'knowledge.estimate.nothing') }}
              </p>
              <div v-if="outcomes.length" class="crawl-outcomes">
                <BcKeyFigure v-for="o in outcomes" :key="o.key" size="sm" :label="$t(`knowledge.estimate.${o.key}`)" :value="formatNumber(o.n)" />
              </div>
              <p v-if="estimate.index_only" class="crawl-muted">{{ $t('knowledge.estimate.indexOnly', { n: estimate.index_only, pages: estimate.max_pages }) }}</p>
              <BcRadioCards v-if="estimate.to_learn && modelOptions.length > 1" v-model="model" :legend="$t('knowledge.models.legend')" :options="modelOptions" :columns="1" />
            </div>
            <div v-if="estimate.to_learn" class="crawl-cost">
              <div class="bc-kf__label">{{ $t('onboarding.learning.cost') }}</div>
              <BcMoney :amount="cost" estimate size="figure" />
              <div class="crawl-cost__row"><span>{{ $t('onboarding.learning.yourBalance') }}</span><BcMoney :amount="balance" size="strong" /></div>
              <div v-if="!balanceShort" class="crawl-cost__row"><span>{{ $t('onboarding.learning.after') }}</span><BcMoney :amount="balance - cost" /></div>
              <BcButton v-if="!balanceShort" variant="primary" size="lg" block :loading="busy" @click="onConfirm">
                {{ $t('knowledge.estimate.learn', { cost: fmtChf(cost) }) }}
              </BcButton>
              <BcButton variant="quiet" block :disabled="busy" @click="onStop">{{ $t('knowledge.job.discard') }}</BcButton>
            </div>
          </div>
        </BcPanel>
        <BcNotice v-if="estimate.to_learn && balanceShort" tone="warning" :title="$t('onboarding.learning.balanceShortTitle')">
          {{ $t('onboarding.learning.balanceShort', { cost: formatCHF(cost), balance: formatCHF(balance) }) }}
          <template #actions>
            <router-link :to="{ name: 'AccountSettings', params: { section: 'billing' } }" class="bc-btn bc-btn--primary bc-btn--sm">{{ $t('onboarding.learning.topUp') }}</router-link>
            <BcButton variant="quiet" size="sm" @click="billing.fetchBalance()">{{ $t('onboarding.learning.recheck') }}</BcButton>
          </template>
        </BcNotice>

        <!-- Gemini's savings suggestions, what was sorted out, and the folder tree -->
        <CrawlSelection :key="job.id" :base="base" :host="displayUrl(job.start_url)" @estimate="onEstimate" />
      </section>

      <!-- Reading: which page (no total, it isn't known yet) -->
      <BcPanel v-if="job.status === 'IN_PROGRESS'">
        <BcActivityLogRow state="running" :title="latestPage(log) ? $t('knowledge.job.reading', { page: latestPage(log) }) : $t('knowledge.job.starting')" />
      </BcPanel>
      <!-- Learning: a real bar, the number of pages is known -->
      <BcPanel v-if="job.status === 'INDEXING'">
        <BcProgressBar tone="ai" :value="progress.done" :max="progress.total || 1" :label="progress.label" />
      </BcPanel>

      <!-- Done: the report -->
      <BcPanel as="section"  v-if="job.status === 'COMPLETED' && job.report" >
        <CrawlReport :report="job.report" />
      </BcPanel>

      <!-- What this crawl brought in, page by page (the latest crawl: the website as the bot knows it) -->
      <BcPanel as="section"  v-if="(job.status === 'COMPLETED' || job.status === 'FAILED') && crawlSources.length"  :title="$t('knowledge.content.title')" :description="$t('knowledge.content.sub')">
        <PageTree :sources="crawlSources" class="crawl-tree" />
      </BcPanel>

      <!-- Activity: live while running, history afterwards -->
      <BcPanel as="section"  >
        <CardTitle as="h2" class="crawl-section-title">{{ $t('knowledge.job.activity') }}</CardTitle>
        <ActivityLog :entries="log" :max-height="isActive ? '560px' : '360px'" />
      </BcPanel>
    </template>

    <ConfirmationModal
      :show="askDelete"
      :title="$t('knowledge.deleteJob.title')"
      :message="$t('knowledge.deleteJob.message', { url: escapeHtml(job?.start_url) })"
      :confirmButtonText="$t('tenant.sources.deleteModal.confirm')"
      :loading="deleting"
      @confirm="onDelete"
      @cancel="askDelete = false"
    />
  </div>
</template>

<script setup>
import { CardTitle } from '@/components/ui/card';
import { computed, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { supabase } from '@/supabase';
import { escapeHtml } from '@/utils/escapeHtml';
import { ACTIVE_STATUSES, isPreparing, learnProgress, useCrawlActions, useCrawlText } from '@/composables/useCrawl';
import ActivityLog from './sources/ActivityLog.vue';
import CrawlReport from './sources/CrawlReport.vue';
import CrawlSelection from './sources/CrawlSelection.vue';
import PageTree from './sources/PageTree.vue';
import { useTenantsStore } from '@/stores/tenants';
import ConfirmationModal from '../ConfirmationModal.vue';
import { useBillingStore } from '@/stores/billing';
import { useToast } from '@/composables/useToast';
import { useLearningModels } from '@/composables/useLearningModels';
import { BcActivityLogRow, BcButton, BcIcon, BcKeyFigure, BcMoney, BcNotice, BcPageHeader, BcPanel, BcProgressBar, BcRadioCards, BcSkeleton, BcStatusBadge } from '@/components/ui';
import { formatCHF, formatNumber } from '@/utils/format';

const props = defineProps({
  tenantId: { type: String, required: true },
  jobId:    { type: [String, Number], required: true },
});
const router = useRouter();
const { t } = useI18n();
const { fmtChf, fmtDateTime, displayUrl, latestPage } = useCrawlText();
const { addToast } = useToast();

// a crawl's status in the design system's badge names
const BADGE = { IN_PROGRESS: 'scanning', SCANNED: 'ready', INDEXING: 'learning', COMPLETED: 'done', FAILED: 'stopped' };
const badge = computed(() => (isPreparing(job.value) ? 'preparing' : BADGE[job.value?.status] || 'stopped'));

// learning is prepaid: the estimate shows what's left afterwards, or how much is missing
const billing = useBillingStore();
billing.fetchBalance();
const balance = computed(() => Number(billing.balance || 0));
const actions = useCrawlActions(() => props.tenantId);

const job = ref(null);
// the learning model the customer picks; reads the job, so it comes after it
const { model, options: modelOptions, cost } = useLearningModels(() => job.value?.estimate, () => useTenantsStore().currentTenant?.learning_model);
const balanceShort = computed(() => balance.value < cost.value);
const log = ref([]);
const loading = ref(false);
const busy = ref(false);
const askDelete = ref(false);
const deleting = ref(false);

// pages and files of this crawl, from the chatbot's sources (reloaded when the crawl ends)
const tenantsStore = useTenantsStore();
const crawlSources = computed(() => (tenantsStore.currentTenant?.tenant_sources || []).filter(
  (s) => s.last_job_id === Number(props.jobId) && (s.source_type === 'URL' || s.source_type === 'FILE_URL')));
const isActive = computed(() => job.value && ACTIVE_STATUSES.includes(job.value.status));
const estimate = computed(() => job.value?.estimate || {});

const OUTCOMES = ['new', 'changed', 'unchanged', 'removed', 'error', 'empty', 'refused', 'unsupported'];
const outcomes = computed(() => {
  const o = { ...(estimate.value.outcomes || {}), removed: estimate.value.removed || 0 };
  return OUTCOMES.filter((k) => o[k]).map((key) => ({ key, n: o[key] }));
});

const progress = computed(() => {
  const { done, total } = learnProgress(job.value, log.value);
  return { done, total, label: t('knowledge.job.learnProgress', { done: formatNumber(done), total: total ? formatNumber(total) : '…' }) };
});

const base = computed(() => `/tenants/${props.tenantId}/crawling_jobs/${props.jobId}`);
const fetchJob = async () => {
  try {
    job.value = (await apiClient.get(base.value)).data;
  } catch { job.value = null; }
};
const fetchLog = async () => {
  try {
    log.value = (await apiClient.get(`${base.value}/log`, { params: { limit: 500 } })).data;
  } catch { /* log is supplementary */ }
};

// Realtime: this job's activity and status; polling while it runs as a safety net
let channel = null;
let poll = null;
const subscribe = () => {
  if (channel) supabase.removeChannel(channel);
  channel = supabase
    .channel(`crawl-${props.jobId}`)
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'crawl_job_log', filter: `job_id=eq.${props.jobId}` }, (payload) => {
      if (!log.value.some((e) => e.id === payload.new.id)) log.value = [...log.value, payload.new];
    })
    .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'crawling_jobs', filter: `id=eq.${props.jobId}` }, fetchJob)
    .subscribe();
};

watch(() => [props.tenantId, props.jobId], async () => {
  loading.value = true;
  await Promise.all([fetchJob(), fetchLog()]);
  loading.value = false;
  subscribe();
}, { immediate: true });

watch(() => job.value?.status, (status) => {
  if (status === 'COMPLETED' || status === 'FAILED') tenantsStore.refetch(props.tenantId);
});
watch(isActive, (active) => {
  clearInterval(poll);
  if (active) poll = setInterval(() => { fetchJob(); fetchLog(); }, 5000);
}, { immediate: true });

onUnmounted(() => {
  if (channel) supabase.removeChannel(channel);
  clearInterval(poll);
});

// ── The selection changed: the estimate comes back recomputed ──
const onEstimate = (estimate) => { job.value = { ...job.value, estimate }; };

const onConfirm = async () => {
  busy.value = true;
  if (await actions.confirm(job.value, model.value)) await fetchJob();
  busy.value = false;
};
const onStop = async () => {
  busy.value = true;
  if (await actions.stop(job.value)) await fetchJob();
  busy.value = false;
};
const onResume = async () => {
  busy.value = true;
  if (await actions.resume(job.value)) await Promise.all([fetchJob(), fetchLog()]);
  busy.value = false;
};
// The dialog stays open while it works: removing hundreds of pages from Gemini takes a while
const onDelete = async () => {
  deleting.value = true;
  const done = await actions.remove(job.value);
  deleting.value = false;
  askDelete.value = false;
  if (done) {
    addToast(t('knowledge.deleteJob.deleted'), 'success');
    router.push({ name: 'TenantSources', params: { tenantId: props.tenantId } });
  }
};
</script>

<style scoped>
.crawl-page { display: flex; flex-direction: column; gap: var(--space-6); }
.crawl-page :deep(.bc-pagehead__title) { overflow-wrap: anywhere; }

.crawl-estimate { display: flex; flex-direction: column; gap: var(--space-4); }
.crawl-estimate__grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: var(--space-8); align-items: start; }
.crawl-estimate__text { display: flex; flex-direction: column; gap: var(--space-4); }
.crawl-estimate__title { font-size: 22px; line-height: 30px; font-weight: 700; }
.crawl-outcomes { display: flex; flex-wrap: wrap; gap: var(--space-4) var(--space-8); }
.crawl-muted { color: var(--text-secondary); max-width: var(--reading-max); }
.crawl-cost { display: flex; flex-direction: column; gap: var(--space-3); padding: var(--space-5); background: var(--surface-2); border-radius: var(--radius-md); }
.crawl-cost__row { display: flex; justify-content: space-between; color: var(--text-secondary); }

.crawl-tree { margin-top: var(--space-4); }
.crawl-section-title { margin-bottom: var(--space-2); }

@media (max-width: 900px) {
  .crawl-estimate__grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
