<template>
  <li class="cjr">
    <BcStatusBadge :status="badge" size="sm" class="cjr__status" />

    <div class="cjr__main">
      <router-link :to="detailRoute" class="cjr__title">{{ displayUrl(job.start_url) }}</router-link>
      <p class="cjr__meta">
        {{ fmtDateTime(job.created_at) }}<template v-if="job.single_page_only"> · {{ $t('knowledge.job.singlePage') }}</template><template v-if="job.trigger === 'scheduled'"> · {{ $t('knowledge.job.autoShort') }}</template>
      </p>

      <!-- Reading: which page, not how many (the total isn't known until the end) -->
      <p v-if="job.status === 'IN_PROGRESS'" class="cjr__now">
        {{ latestPage(log) ? $t('knowledge.job.reading', { page: latestPage(log) }) : $t('knowledge.job.starting') }}
      </p>
      <!-- Learning: the number of pages is known, so a real bar -->
      <div v-else-if="job.status === 'INDEXING'" class="cjr__live">
        <BcProgressBar tone="ai" :value="progress.done" :max="progress.total || 1" :label="progress.label" :detail="currentActivity(log)" />
      </div>
      <p v-else-if="isPreparing(job)" class="cjr__now">{{ $t('knowledge.estimate.preparing') }}</p>
      <p v-else class="cjr__summary">
        {{ jobSummary(job) }}
        <BcStatusBadge v-if="reviewCount" status="warn" size="sm" :label="$t('knowledge.job.toReview', { n: reviewCount })" />
      </p>
    </div>

    <div class="cjr__actions">
      <BcButton v-if="job.status === 'SCANNED' && job.estimate?.to_learn" variant="primary" size="sm" :loading="busy" @click="onConfirm">
        {{ $t('knowledge.estimate.learn', { cost: fmtChf(job.estimate.cost_chf) }) }}
      </BcButton>
      <BcButton v-if="job.status === 'FAILED'" variant="secondary" size="sm" icon="play" :loading="busy" @click="onResume">{{ $t('knowledge.job.resume') }}</BcButton>
      <Button as-child variant="ghost" size="sm"><router-link :to="detailRoute" >{{ $t('knowledge.job.details') }}</router-link></Button>
    </div>
  </li>
</template>

<script setup>
import { Button } from '@/components/ui/button';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { isPreparing, learnProgress, useCrawlActions, useCrawlText } from '@/composables/useCrawl';
import { BcButton, BcProgressBar, BcStatusBadge } from '@/components/ui';
import { formatNumber } from '@/utils/format';

// a crawl's status in the design system's badge names
const BADGE = { IN_PROGRESS: 'scanning', SCANNED: 'ready', INDEXING: 'learning', COMPLETED: 'done', FAILED: 'stopped' };

const props = defineProps({
  job:      { type: Object, required: true },
  tenantId: { type: String, required: true },
  log:      { type: Array, default: () => [] },
});
const emit = defineEmits(['changed']);
const { t } = useI18n();
const { fmtChf, fmtDateTime, displayUrl, currentActivity, latestPage, jobSummary } = useCrawlText();
const { confirm, resume } = useCrawlActions(() => props.tenantId);

const busy = ref(false);
const badge = computed(() => (isPreparing(props.job) ? 'preparing' : BADGE[props.job.status] || 'stopped'));
const detailRoute = computed(() => ({ name: 'TenantCrawl', params: { tenantId: props.tenantId, jobId: props.job.id } }));
const reviewCount = computed(() => (props.job.status === 'COMPLETED' ? (props.job.report?.attention || []).filter((a) => a.kind).length : 0));

// Learning only: learned / to learn (known from the estimate)
const progress = computed(() => {
  const { done, total } = learnProgress(props.job, props.log);
  return { done, total, label: t('knowledge.job.learnProgress', { done: formatNumber(done), total: total ? formatNumber(total) : '…' }) };
});

const onConfirm = async () => {
  busy.value = true;
  if (await confirm(props.job)) emit('changed');
  busy.value = false;
};
const onResume = async () => {
  busy.value = true;
  if (await resume(props.job)) emit('changed');
  busy.value = false;
};
</script>

<style scoped>
.cjr {
  display: grid; grid-template-columns: 168px minmax(0, 1fr) auto; align-items: start; gap: var(--space-4);
  padding: var(--space-4) 0; border-top: 1px solid var(--border-subtle);
}
.cjr:first-child { border-top: none; padding-top: var(--space-1); }
.cjr__status { justify-self: start; margin-top: 2px; }
.cjr__main { min-width: 0; }
.cjr__title {
  display: block; font-weight: 700; color: var(--text-primary); text-decoration: none;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cjr__title:hover { color: var(--interactive); text-decoration: underline; }
.cjr__meta { font-size: 14px; line-height: 20px; color: var(--text-secondary); }
.cjr__summary { margin-top: var(--space-2); display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2); }
.cjr__now { margin-top: var(--space-2); color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cjr__live { margin-top: var(--space-3); max-width: 520px; }
.cjr__actions { display: flex; align-items: center; gap: var(--space-2); }

@media (max-width: 760px) {
  .cjr { grid-template-columns: minmax(0, 1fr); gap: var(--space-2); }
  .cjr__actions { flex-wrap: wrap; }
}
</style>
