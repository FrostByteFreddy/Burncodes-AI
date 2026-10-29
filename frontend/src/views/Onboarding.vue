<template>
  <div class="onb">
    <div class="onb-inner">
    <!-- Brand panel, as on the login page: logo, the steps, leave for later -->
    <aside class="onb-brand">
      <img src="/logo_white.svg" alt="Burncodes AI" class="onb-brand__logo" />
      <ol class="onb-steps" :aria-label="$t('ui.setup')">
        <li v-for="(name, i) in stepNames" :key="i" :class="{ 'is-done': i < progress.step, 'is-current': i === progress.step }"
          :aria-current="i === progress.step ? 'step' : undefined">
          <span class="onb-steps__num" aria-hidden="true"><BcIcon v-if="i < progress.step" name="check" /><template v-else>{{ i + 1 }}</template></span>
          {{ name }}<span v-if="i < progress.step" class="bc-sr"> {{ $t('ui.doneSr') }}</span>
        </li>
      </ol>
      <p class="onb-brand__compact">{{ $t('ui.stepOf', { n: progress.step + 1, total: STEPS.length }) }} · <strong>{{ stepNames[progress.step] }}</strong></p>
      <button type="button" class="onb-later" @click="leave">{{ $t('onboarding.later') }}</button>
    </aside>

    <main :class="['onb-body', { 'onb-body--wide': WIDE.includes(step) }]">
      <div class="onb-col">
        <div class="onb-head">
          <h1 class="onb-title">{{ $t(`onboarding.${step}.title`) }}</h1>
          <p class="onb-lede">{{ $t(`onboarding.${step}.lede`) }}</p>
        </div>

        <!-- Welcome: what happens and what it costs -->
        <ol v-if="step === 'welcome'" class="onb-overview">
          <li v-for="key in OVERVIEW" :key="key.id">
            <span :class="['onb-overview__icon', { 'is-ai': key.id === 'learn' }]"><BcIcon :name="key.icon" /></span>
            <span>
              <strong>{{ $t(`onboarding.welcome.points.${key.id}.title`) }}</strong>
              <span>{{ $t(`onboarding.welcome.points.${key.id}.text`) }}</span>
            </span>
          </li>
        </ol>

        <!-- Basics: name, website, audience -->
        <div v-if="step === 'basics'" class="onb-fields">
          <BcTextInput v-model="basics.name" :label="$t('onboarding.basics.name')" :hint="$t('onboarding.basics.nameHint')"
            :placeholder="$t('onboarding.basics.namePlaceholder')" />
          <BcUrlInput v-model="basics.url" :label="$t('onboarding.basics.url')" :placeholder="$t('onboarding.basics.urlPlaceholder')"
            :hint="$t('onboarding.basics.urlHint')" :error="basics.url && !urlValid ? $t('tenant.sources.invalidUrl') : ''"
            :state="basics.url && !urlValid ? 'invalid' : ''" />
          <BcRadioCards v-model="basics.audience" :legend="$t('configure.basics.audience')" :options="audienceOptions" />
        </div>

        <!-- Reading: how much of the website, with the recommended options -->
        <div v-if="step === 'reading'" class="onb-fields">
          <BcNotice v-if="progress.jobId" tone="success" :title="$t('onboarding.reading.started', { url: displayUrl(progress.url) })" />
          <template v-else>
            <BcRadioCards v-model="reading.single" :options="scopeOptions" />
            <div v-if="!reading.single">
              <BcCheckboxRow v-for="key in ['useSitemap', 'sameLanguage', 'skipFunnel']" :key="key" v-model="reading[key]" recommended
                :title="$t(`tenant.sources.wizard.options.${key}`)" :description="$t(`tenant.sources.wizard.options.${key}Desc`)" />
            </div>
            <BcDisclosure :title="$t('onboarding.reading.more')" :meta="moreMeta">
              <div class="onb-fields">
                <BcTextarea v-if="!reading.single" v-model="reading.excluded" :rows="3" :label="$t('tenant.sources.wizard.exclude.title')"
                  :hint="$t('onboarding.reading.excludeHint')" :placeholder="$t('onboarding.reading.excludePlaceholder')" optional />
                <BcCheckboxRow v-model="reading.thorough" :title="$t('tenant.sources.wizard.modePlaywright')" :description="$t('tenant.sources.wizard.modePlaywrightDesc')" />
              </div>
            </BcDisclosure>
          </template>
        </div>

        <!-- Look: website branding, tone, greeting -->
        <div v-if="step === 'look'" class="onb-fields">
          <BcNotice v-if="branding === 'loading'" tone="info" icon="spinner" :title="$t('onboarding.look.branding')" />
          <BcNotice v-else-if="branding === 'found'" tone="success" :title="$t('onboarding.look.brandingFound')" />
          <BcNotice v-else-if="branding === 'none'" tone="info">{{ $t('onboarding.look.brandingNone') }}</BcNotice>
          <template v-if="form">
            <BcRadioCards :model-value="activeTone" :legend="$t('configure.tone.title')" :options="toneOptions" :columns="1"
              @update:model-value="(k) => (form.system_persona = TONES[k])" />
            <BcTextarea v-model="form.intro_message" :rows="3" :label="$t('onboarding.look.greeting')" :hint="$t('onboarding.look.greetingHint')" />
          </template>
        </div>

        <!-- Learning: progress, estimate, start -->
        <div v-if="step === 'learning'" class="onb-fields">
          <BcProgressBar v-if="!job || job.status === 'IN_PROGRESS'" :value="jobProgress ? jobProgress.completed + jobProgress.failed : 0"
            :max="jobProgress?.total || 1" :label="jobProgress ? $t('onboarding.learning.pagesRead', { done: formatNumber(jobProgress.completed + jobProgress.failed), total: formatNumber(jobProgress.total) }) : $t('onboarding.learning.starting')"
            :hide-percent="!jobProgress" :detail="$t('onboarding.learning.reading')" />
          <BcNotice v-else-if="isPreparing(job)" tone="info" icon="spinner" :title="$t('onboarding.learning.estimating')" />
          <template v-else-if="job.status === 'SCANNED'">
            <BcPanel v-if="estimate.to_learn">
              <div class="onb-estimate">
                <div>
                  <h2 class="onb-estimate__title">{{ $t('onboarding.learning.estimateTitle', { n: formatNumber(estimate.to_learn) }) }}</h2>
                  <p class="onb-muted">{{ $t('onboarding.learning.estimateBody') }}</p>
                  <BcRadioCards v-if="modelOptions.length > 1" v-model="model" class="onb-models" :legend="$t('knowledge.models.legend')" :options="modelOptions" :columns="1" />
                </div>
                <div class="onb-cost">
                  <div class="bc-kf__label">{{ $t('onboarding.learning.cost') }}</div>
                  <BcMoney :amount="cost" estimate size="figure" />
                  <div class="onb-cost__row"><span>{{ $t('onboarding.learning.yourBalance') }}</span><BcMoney :amount="Number(billing.balance || 0)" size="strong" /></div>
                  <div v-if="!balanceShort" class="onb-cost__row"><span>{{ $t('onboarding.learning.after') }}</span><BcMoney :amount="Number(billing.balance || 0) - cost" /></div>
                  <BcButton v-if="!balanceShort" variant="primary" size="lg" block :loading="confirming" @click="startLearning">
                    {{ $t('onboarding.learning.start', { cost: formatCHF(cost) }) }}
                  </BcButton>
                  <a :href="crawlHref" target="_blank" rel="noopener" class="bc-btn bc-btn--quiet bc-btn--md bc-btn--block">{{ $t('onboarding.learning.choose') }}</a>
                </div>
              </div>
            </BcPanel>
            <BcNotice v-else tone="info" :title="$t('onboarding.learning.nothing')" />
            <BcNotice v-if="estimate.to_learn && balanceShort" tone="warning" :title="$t('onboarding.learning.balanceShortTitle')">
              {{ $t('onboarding.learning.balanceShort', { cost: formatCHF(cost), balance: formatCHF(billing.balance) }) }}
              <template #actions>
                <a :href="billingHref" target="_blank" rel="noopener" class="bc-btn bc-btn--primary bc-btn--sm">{{ $t('onboarding.learning.topUp') }}</a>
                <BcButton variant="quiet" size="sm" @click="billing.fetchBalance()">{{ $t('onboarding.learning.recheck') }}</BcButton>
              </template>
            </BcNotice>
          </template>
          <BcProgressBar v-else-if="job.status === 'INDEXING'" tone="ai" :value="job.learn_done || 0" :max="estimate.to_learn || 1"
            :label="$t('onboarding.learning.learned', { done: formatNumber(job.learn_done || 0), total: formatNumber(estimate.to_learn || 0) })"
            :detail="$t('onboarding.learning.learning')" />
          <BcNotice v-else-if="job.status === 'COMPLETED'" tone="success" :title="$t('onboarding.learning.done')" />
          <BcNotice v-else tone="warning" :title="$t('onboarding.learning.stopped')">
            <template #actions><a :href="crawlHref" target="_blank" rel="noopener" class="bc-btn bc-btn--secondary bc-btn--sm">{{ $t('onboarding.learning.details') }}</a></template>
          </BcNotice>
        </div>

        <!-- Try: the real chat beside -->
        <BcNotice v-if="step === 'try' && job?.status !== 'COMPLETED'" tone="warning" icon="hourglass-half" :title="$t('onboarding.try.notYet')" />

        <!-- Install: the existing instructions -->
        <div v-if="step === 'install' && tenant" class="onb-install"><Install /></div>

        <!-- Done -->
        <ul v-if="step === 'done'" class="onb-next">
          <li v-for="key in ['knowledge', 'look', 'insights']" :key="key"><BcIcon name="arrow-right" /> {{ $t(`onboarding.done.next.${key}`) }}</li>
        </ul>

        <BcNotice v-if="tips.length" tone="tip">
          <ul class="onb-tips"><li v-for="(tip, i) in tips" :key="i">{{ tip }}</li></ul>
        </BcNotice>

        <footer class="onb-nav">
          <BcButton v-if="progress.step > 0 && step !== 'done'" variant="secondary" size="lg" icon="arrow-left" :disabled="busy" @click="progress.step--">
            {{ $t('onboarding.back') }}
          </BcButton>
          <span class="onb-nav__gap"></span>
          <BcButton variant="brand" size="lg" :icon-right="step === 'done' ? '' : 'arrow-right'" :loading="busy" :disabled="!canContinue" @click="next">
            {{ nextLabel }}
          </BcButton>
        </footer>
      </div>

      <!-- Preview beside the content on Aussehen and Ausprobieren -->
      <aside v-if="step === 'look' && form" class="onb-preview">
        <EditablePreview :form="form" :tenant-id="progress.tenantId" />
      </aside>
      <aside v-if="step === 'try' && tenant" class="onb-preview">
        <ChatPreview :config="tenant.widget_config || {}" :tenant-id="progress.tenantId" />
      </aside>
    </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import apiClient from '../utils/api';
import { useTenantsStore } from '../stores/tenants';
import { useBillingStore } from '../stores/billing';
import { useToast } from '../composables/useToast';
import { isPreparing, useCrawlActions } from '../composables/useCrawl';
import { useLearningModels } from '../composables/useLearningModels';
import { AUDIENCES, TONES, defaultsFor } from '../utils/chatbotDefaults';
import { applyBranding, fromTenant } from '../utils/widgetConfig';
import { endOnboarding, loadProgress, pauseOnboarding, saveProgress } from '../utils/onboarding';
import EditablePreview from '../components/tenant/settings/EditablePreview.vue';
import {
  BcButton, BcCheckboxRow, BcDisclosure, BcIcon, BcMoney, BcNotice, BcPanel, BcProgressBar, BcRadioCards,
  BcTextarea, BcTextInput, BcUrlInput,
} from '../components/ui';
import { formatCHF, formatNumber } from '../utils/format';
import ChatPreview from '../components/tenant/ChatPreview.vue';
import Install from './Install.vue';

const STEPS = ['welcome', 'basics', 'reading', 'look', 'learning', 'try', 'install', 'done'];
// the design system's icon per concept; learning is the AI's, so magenta
const OVERVIEW = [
  { id: 'create', icon: 'layer-group' }, { id: 'read', icon: 'globe' }, { id: 'look', icon: 'sliders' },
  { id: 'learn', icon: 'brain' }, { id: 'install', icon: 'code' },
];
// steps with a preview beside the content
const WIDE = ['look', 'try'];

const { t, tm, rt, locale } = useI18n();
const router = useRouter();
const tenantsStore = useTenantsStore();
const billing = useBillingStore();
const { addToast } = useToast();
const actions = useCrawlActions(() => progress.tenantId);

// ── Progress, kept across reloads ───────────────────────────────────
const progress = reactive({ step: 0, tenantId: null, jobId: null, url: '', branded: false, ...loadProgress() });
progress.step = Math.min(Math.max(Number(progress.step) || 0, 0), STEPS.length - 1);
watch(progress, () => saveProgress({ ...progress }), { deep: true });

const step = computed(() => STEPS[progress.step]);
const tenant = computed(() => (tenantsStore.currentTenant?.id === progress.tenantId ? tenantsStore.currentTenant : null));
const tips = computed(() => (tm(`onboarding.${step.value}.tips`) || []).map((m) => rt(m)));
const busy = ref(false);

if (progress.tenantId) tenantsStore.fetchTenant(progress.tenantId);

const stepNames = computed(() => STEPS.map((s) => t(`onboarding.${s}.short`)));
const displayUrl = (url) => (url || '').replace(/^https?:\/\//, '').replace(/\/$/, '');

// ── Basics ──────────────────────────────────────────────────────────
const basics = reactive({ name: '', url: progress.url || '', audience: null });
watch(tenant, (tn) => {
  if (!tn) return;
  if (!basics.name) basics.name = tn.name || '';
  if (!basics.audience) basics.audience = tn.audience || null;
}, { immediate: true });

const finalUrl = computed(() => {
  const u = basics.url.trim();
  return u && !/^https?:\/\//i.test(u) ? `https://${u}` : u;
});
const urlValid = computed(() => {
  try { return ['http:', 'https:'].includes(new URL(finalUrl.value).protocol) && finalUrl.value.includes('.'); } catch { return false; }
});

async function saveBasics() {
  const fields = { name: basics.name.trim(), audience: basics.audience };
  if (progress.tenantId) {
    await tenantsStore.updateTenant(progress.tenantId, fields);
  } else {
    const created = await tenantsStore.createTenant({ ...defaultsFor(locale.value), ...fields });
    progress.tenantId = created.id;
    await tenantsStore.fetchTenant(created.id);
  }
  if (finalUrl.value !== progress.url) {
    // another website: read it afresh and take its look again
    progress.url = finalUrl.value;
    progress.jobId = null;
    progress.branded = false;
  }
}

const audienceOptions = computed(() => AUDIENCES.map((key) => ({
  value: key, icon: key === 'municipality' ? 'landmark' : 'store',
  title: t(`configure.basics.audiences.${key}`), description: t(`configure.basics.audiences.${key}Desc`),
})));

// ── Reading ─────────────────────────────────────────────────────────
const reading = reactive({ single: false, useSitemap: true, sameLanguage: true, skipFunnel: true, excluded: '', thorough: false });

const scopeOptions = computed(() => [
  { value: false, title: t('tenant.sources.wizard.scope.fullTitle'), description: t('tenant.sources.wizard.scope.fullDesc') },
  { value: true, title: t('tenant.sources.wizard.singlePageLabel'), description: t('tenant.sources.wizard.scope.singleDesc') },
]);
const moreMeta = computed(() => [!reading.single && t('tenant.sources.wizard.exclude.title'), t('tenant.sources.wizard.modePlaywright')].filter(Boolean).join(' · '));

// "shop.example.com" or "https://…" stays as typed; anything else is a path
const toExclusion = (line) => (/^https?:\/\//.test(line) || (!line.startsWith('/') && line.split('/')[0].includes('.'))
  ? line : `/${line.replace(/^\/+/, '')}`);

async function startReading() {
  const full = !reading.single;
  await apiClient.post(`/tenants/${progress.tenantId}/sources/discover`, {
    url: progress.url,
    single_page_only: reading.single,
    excluded_urls: full ? reading.excluded.split('\n').map((l) => l.trim()).filter(Boolean).map(toExclusion) : [],
    same_language: full && reading.sameLanguage,
    use_sitemap: full && reading.useSitemap,
    skip_funnel: full && reading.skipFunnel,
    crawl_mode: reading.thorough ? 'playwright' : 'soup',
  });
  // the job is created in the background; wait for it briefly
  for (let i = 0; i < 15 && !progress.jobId; i++) {
    const { data } = await apiClient.get(`/tenants/${progress.tenantId}/crawling_jobs`);
    if (data?.length) progress.jobId = data[0].id;
    else await new Promise((r) => setTimeout(r, 2000));
  }
}

// ── Look ────────────────────────────────────────────────────────────
const form = ref(null);
const branding = ref('');

async function prepareLook() {
  if (!progress.tenantId) return;
  if (!tenant.value) await tenantsStore.fetchTenant(progress.tenantId);
  form.value = fromTenant(tenant.value || {});
  if (progress.branded) return;
  branding.value = 'loading';
  try {
    const { data } = await apiClient.post(`/tenants/${progress.tenantId}/branding`, { url: progress.url });
    branding.value = applyBranding(form.value.widget_config, data) ? 'found' : 'none';
  } catch {
    branding.value = 'none';
  }
}

const toneOptions = computed(() => Object.keys(TONES).map((key) => ({
  value: key, title: t(`configure.tone.${key}`), description: t(`configure.tone.${key}Desc`),
})));
const activeTone = computed(() => Object.keys(TONES).find((k) => TONES[k] === (form.value?.system_persona || '').trim()) || null);

async function saveLook() {
  await tenantsStore.updateTenant(progress.tenantId, form.value);
  progress.branded = true;
}

// ── Learning: polled while it's on screen ───────────────────────────
const job = ref(null);
const jobProgress = ref(null);
const confirming = ref(false);
let timer = null;

const estimate = computed(() => job.value?.estimate || {});
const { model, options: modelOptions, cost } = useLearningModels(() => job.value?.estimate, () => tenant.value?.learning_model);
const balanceShort = computed(() => Number(billing.balance) < cost.value);

async function poll() {
  if (!progress.tenantId || !progress.jobId) return;
  const base = `/tenants/${progress.tenantId}/crawling_jobs/${progress.jobId}`;
  try {
    job.value = (await apiClient.get(base)).data;
    if (job.value.status === 'IN_PROGRESS') jobProgress.value = (await apiClient.get(`${base}/progress`)).data;
  } catch (e) {
    if (e.response?.status === 404) progress.jobId = null;   // deleted meanwhile
  }
}

async function startLearning() {
  confirming.value = true;
  try {
    if (await actions.confirm(job.value, model.value)) await poll();
  } finally {
    confirming.value = false;
  }
}

const billingHref = computed(() => router.resolve({ name: 'AccountSettings', params: { section: 'billing' } }).href);
const crawlHref = computed(() => (progress.jobId
  ? router.resolve({ name: 'TenantCrawl', params: { tenantId: progress.tenantId, jobId: progress.jobId } }).href : '#'));

// ── Moving between steps ────────────────────────────────────────────
watch(step, (s) => {
  clearInterval(timer);
  timer = null;
  if (s === 'look') prepareLook();
  if (['learning', 'try'].includes(s)) {
    poll();
    if (s === 'learning') {
      billing.fetchBalance();
      timer = setInterval(poll, 6000);
    }
  }
  window.scrollTo({ top: 0 });
}, { immediate: true });
onBeforeUnmount(() => clearInterval(timer));

const canContinue = computed(() => {
  if (step.value === 'basics') return basics.name.trim() && urlValid.value && basics.audience;
  if (step.value === 'look') return Boolean(form.value) && branding.value !== 'loading';
  return true;
});

const nextLabel = computed(() => {
  if (step.value === 'welcome') return t('onboarding.welcome.start');
  if (step.value === 'reading' && !progress.jobId) return t('onboarding.reading.start');
  if (step.value === 'learning' && job.value?.status !== 'COMPLETED') return t('onboarding.learning.continue');
  if (step.value === 'done') return t('onboarding.done.finish');
  return t('onboarding.next');
});

async function next() {
  busy.value = true;
  try {
    if (step.value === 'basics') await saveBasics();
    if (step.value === 'reading' && !progress.jobId) await startReading();
    if (step.value === 'look') await saveLook();
    if (step.value === 'done') return finish();
    progress.step++;
  } catch (e) {
    addToast(e.response?.data?.error || t('onboarding.failed'), 'error');
  } finally {
    busy.value = false;
  }
}

function finish() {
  const id = progress.tenantId;
  endOnboarding();
  router.push(id ? { name: 'TenantOverview', params: { tenantId: id } } : '/manage-tenants');
}

function leave() {
  pauseOnboarding();
  router.push(progress.tenantId ? { name: 'TenantOverview', params: { tenantId: progress.tenantId } } : '/manage-tenants');
}
</script>

<style scoped>
/* Brand panel and work surface sit in one centred column, as in the dashboard;
   only the gradient behind the panel runs out to the left edge of the screen */
.onb { --onb-max: var(--shell-max); --onb-panel: 320px; position: relative; min-height: 100dvh; background: var(--surface-1); }
.onb::before {
  content: ''; position: absolute; top: 0; bottom: 0; left: 0;
  width: calc(max(0px, (100% - var(--onb-max)) / 2) + var(--onb-panel));
  background: linear-gradient(160deg, var(--brand-indigo) 0%, var(--brand-violet) 45%, var(--brand-magenta) 100%);
}
.onb-inner {
  position: relative; max-width: var(--onb-max); margin: 0 auto; min-height: 100dvh;
  display: grid; grid-template-columns: var(--onb-panel) minmax(0, 1fr);
}

/* ── Brand panel ── */
.onb-brand {
  position: sticky; top: 0; height: 100dvh; overflow: hidden;
  display: flex; flex-direction: column; gap: var(--space-10);
  padding: var(--space-10) var(--space-8); color: #fff;
}
.onb-brand__logo { position: relative; height: 40px; width: auto; align-self: flex-start; }
.onb-steps { position: relative; list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-1); }
.onb-steps li {
  display: flex; align-items: center; gap: var(--space-3); min-height: 40px; padding: 0 var(--space-3);
  border-radius: var(--radius-md); font-weight: 600; color: rgba(255, 255, 255, 0.72);
}
.onb-steps li.is-done { color: rgba(255, 255, 255, 0.92); }
.onb-steps li.is-current { background: rgba(255, 255, 255, 0.16); color: #fff; }
.onb-steps__num {
  width: 26px; height: 26px; flex: none; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center; font-size: 13px;
  border: 1.5px solid rgba(255, 255, 255, 0.6);
}
.is-current .onb-steps__num { background: #fff; color: var(--brand-indigo); border-color: #fff; }
.is-done .onb-steps__num { background: rgba(255, 255, 255, 0.24); border-color: transparent; }
.onb-brand__compact { display: none; }
.onb-later {
  position: relative; margin-top: auto; align-self: flex-start;
  font: inherit; font-weight: 600; color: #fff; background: none; border: none; padding: var(--space-2) 0;
  text-decoration: underline; text-underline-offset: 3px; cursor: pointer;
}
.onb-later:focus-visible { outline-color: #fff; }

/* ── Work surface ── */
.onb-body { width: 100%; max-width: var(--reading-max); margin: 0 auto; padding: var(--space-16) var(--space-8); }
.onb-body--wide {
  max-width: calc(var(--reading-max) + var(--widget-width) + var(--space-12));
  display: grid; grid-template-columns: minmax(0, 1fr) var(--widget-width); gap: var(--space-12); align-items: start;
}
.onb-col { display: flex; flex-direction: column; gap: var(--space-6); min-width: 0; }

.onb-title { font-size: 32px; line-height: 40px; font-weight: 700; letter-spacing: -0.01em; color: var(--text-primary); }
.onb-lede { margin-top: var(--space-2); font-size: 18px; line-height: 28px; color: var(--text-secondary); }
.onb-muted { color: var(--text-secondary); }
.onb-fields { display: flex; flex-direction: column; gap: var(--space-6); }

.onb-overview { list-style: none; padding: 0; display: flex; flex-direction: column; gap: var(--space-5); }
.onb-overview li { display: flex; gap: var(--space-4); align-items: flex-start; }
.onb-overview strong { display: block; }
.onb-overview li span:last-child span { color: var(--text-secondary); }
.onb-overview__icon {
  width: 40px; height: 40px; flex: none; border-radius: var(--radius-md);
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--interactive-soft); color: var(--interactive);
}
.onb-overview__icon.is-ai { background: var(--ai-soft); color: var(--ai); }

.onb-estimate { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: var(--space-8); align-items: start; }
.onb-models { margin-top: var(--space-5); }
.onb-estimate__title { font-size: 22px; line-height: 30px; font-weight: 700; margin-bottom: var(--space-2); }
.onb-cost { display: flex; flex-direction: column; gap: var(--space-3); padding: var(--space-5); background: var(--surface-2); border-radius: var(--radius-md); }
.onb-cost__row { display: flex; justify-content: space-between; color: var(--text-secondary); }

.onb-tips { margin: 0; padding-left: var(--space-5); display: flex; flex-direction: column; gap: var(--space-1); }
.onb-next { list-style: none; padding: 0; display: flex; flex-direction: column; gap: var(--space-3); }
.onb-next li { display: flex; gap: var(--space-3); align-items: baseline; }
.onb-next :deep(.bc-icon) { color: var(--interactive); }

.onb-install :deep(.page-head) { display: none; }   /* the step already has a title */

.onb-nav { display: flex; align-items: center; gap: var(--space-3); padding-top: var(--space-2); }
.onb-nav__gap { flex: 1; }

.onb-preview { position: sticky; top: var(--space-10); height: min(640px, calc(100dvh - var(--space-16))); display: flex; flex-direction: column; }

@media (max-width: 1300px) {
  .onb-body--wide { display: block; max-width: var(--reading-max); }
  .onb-preview { position: static; height: 560px; margin-top: var(--space-8); }
}
@media (max-width: 900px) {
  /* the brand panel becomes a gradient top bar */
  .onb::before { display: none; }
  .onb-inner { grid-template-columns: minmax(0, 1fr); }
  .onb-brand {
    position: sticky; top: 0; height: auto; z-index: var(--z-sticky);
    background: linear-gradient(160deg, var(--brand-indigo) 0%, var(--brand-violet) 45%, var(--brand-magenta) 100%);
    flex-direction: row; align-items: center; gap: var(--space-4); padding: var(--space-3) var(--space-4);
  }
  .onb-brand__logo { height: 28px; }
  .onb-steps { display: none; }
  .onb-brand__compact { display: block; position: relative; flex: 1; min-width: 0; font-size: 14px; line-height: 20px; color: rgba(255, 255, 255, 0.85); }
  .onb-later { margin-top: 0; font-size: 14px; }
  .onb-estimate { grid-template-columns: minmax(0, 1fr); }
  .onb-body { padding: var(--space-8) var(--space-4) var(--space-12); }
}
@media (max-width: 600px) {
  .onb-title { font-size: 28px; line-height: 36px; }
  .onb-brand__compact strong { display: none; }
}
</style>
