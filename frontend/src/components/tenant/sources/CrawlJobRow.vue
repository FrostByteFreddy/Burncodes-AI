<template>
  <li class="cjr" :class="`cjr--${job.status.toLowerCase()}`">
    <span class="cjr__status" :class="`cjr__status--${job.status.toLowerCase()}`">
      <font-awesome-icon v-if="job.status === 'IN_PROGRESS' || job.status === 'INDEXING'" :icon="['fas', 'spinner']" class="animate-spin" />
      {{ $t(`knowledge.status.${job.status}`) }}
    </span>

    <div class="cjr__main">
      <router-link :to="detailRoute" class="cjr__title">{{ displayUrl(job.start_url) }}</router-link>
      <p class="cjr__meta">
        {{ fmtDateTime(job.created_at) }}<template v-if="job.single_page_only">, {{ $t('knowledge.job.singlePage').toLowerCase() }}</template><template v-if="job.trigger === 'scheduled'">, {{ $t('knowledge.job.autoShort') }}</template>
      </p>

      <!-- Running: progress + what is happening right now -->
      <div v-if="job.status === 'IN_PROGRESS' || job.status === 'INDEXING'" class="cjr__live">
        <div class="cjr__bar"><div class="cjr__bar-fill" :style="{ width: progress + '%' }"></div></div>
        <p class="cjr__now">{{ currentActivity(log) || $t('knowledge.log.empty') }}</p>
      </div>
      <p v-else class="cjr__summary">
        {{ jobSummary(job) }}
        <span v-if="reviewCount" class="cjr__review">{{ $t('knowledge.job.toReview', { n: reviewCount }) }}</span>
      </p>
    </div>

    <div class="cjr__actions">
      <button v-if="job.status === 'SCANNED' && job.estimate?.to_learn" class="btn-action" :disabled="busy" @click="onConfirm">
        <font-awesome-icon v-if="busy" :icon="['fas', 'spinner']" class="animate-spin" />
        {{ $t('knowledge.estimate.learn', { cost: fmtChf(job.estimate.cost_chf) }) }}
      </button>
      <router-link :to="detailRoute" class="btn-quiet">{{ $t('knowledge.job.details') }}</router-link>
    </div>
  </li>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useCrawlActions, useCrawlText } from '@/composables/useCrawl';

const props = defineProps({
  job:      { type: Object, required: true },
  tenantId: { type: String, required: true },
  log:      { type: Array, default: () => [] },
});
const emit = defineEmits(['changed']);
const { fmtChf, fmtDateTime, displayUrl, currentActivity, jobSummary } = useCrawlText();
const { confirm } = useCrawlActions(() => props.tenantId);

const busy = ref(false);
const detailRoute = computed(() => ({ name: 'TenantCrawl', params: { tenantId: props.tenantId, jobId: props.job.id } }));
const reviewCount = computed(() => (props.job.status === 'COMPLETED' ? props.job.report?.attention?.length || 0 : 0));

// Scan: scanned / discovered so far; learning: learned / to learn
const progress = computed(() => {
  if (props.job.status === 'INDEXING') {
    const total = props.job.estimate?.to_learn || 0;
    const done = props.log.filter((e) => e.event === 'learned' || e.event === 'learn_failed').length;
    return total ? Math.min(100, (done / total) * 100) : 0;
  }
  const started = props.log.filter((e) => e.event === 'scan').length;
  const done = props.log.filter((e) => e.event === 'scanned').length;
  return started ? Math.min(100, (done / Math.max(started, props.job.task_count || 0)) * 100) : 0;
});

const onConfirm = async () => {
  busy.value = true;
  if (await confirm(props.job)) emit('changed');
  busy.value = false;
};
</script>

<style scoped>
.cjr {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr) auto;
  align-items: start;
  gap: 16px;
  padding: 16px 0;
  border-top: 1px solid var(--surface-3);
}
.cjr:first-child { border-top: none; padding-top: 4px; }

.cjr__status {
  justify-self: start;
  display: inline-flex; align-items: center; gap: 6px;
  margin-top: 2px; padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs); font-weight: 700;
  background: var(--surface-2); color: var(--surface-text);
}
.cjr__status--in_progress, .cjr__status--indexing { background: var(--ai-soft); color: var(--ai); }
.cjr__status--scanned { background: var(--interactive-soft); color: var(--interactive); }
.cjr__status--completed { background: var(--status-success-soft); color: var(--status-success); }
.cjr__status--failed { background: var(--status-warning-soft); color: var(--status-warning); }

.cjr__main { min-width: 0; }
.cjr__title {
  display: block; font-size: 15px; font-weight: 700; color: var(--surface-heading);
  text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cjr__title:hover { color: var(--interactive); text-decoration: underline; }
.cjr__meta { margin-top: 2px; font-size: var(--text-sm); color: var(--surface-muted); }
.cjr__summary { margin-top: 6px; font-size: var(--text-sm); color: var(--surface-text); }
.cjr__review {
  margin-left: 8px; padding: 1px 8px; border-radius: var(--radius-pill);
  font-size: var(--text-xs); font-weight: 700;
  background: var(--status-warning-soft); color: var(--status-warning);
}

.cjr__live { margin-top: 10px; max-width: 520px; }
.cjr__bar { height: 4px; border-radius: var(--radius-pill); background: var(--surface-3); overflow: hidden; }
.cjr__bar-fill { height: 100%; width: 0; background: var(--ai); transition: width var(--t-slow); }
.cjr__now { margin-top: 6px; font-size: var(--text-sm); color: var(--surface-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.cjr__actions { display: flex; align-items: center; gap: 8px; }
.cjr__actions .btn-quiet { text-decoration: none; }

@media (max-width: 760px) {
  .cjr { grid-template-columns: minmax(0, 1fr); gap: 8px; }
  .cjr__actions { flex-wrap: wrap; }
}
</style>
