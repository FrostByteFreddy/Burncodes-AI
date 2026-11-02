<template>
  <WizardPanel
    :open="open"
    :title="$t('tenant.sources.wizard.addKnowledge')"
    :step="step"
    :total-steps="lastStep + 1"
    :can-proceed="canProceed"
    :can-submit="!submitting"
    :submitting="submitting"
    :back-label="$t('tenant.sources.wizard.back')"
    :next-label="$t('tenant.sources.wizard.next')"
    :submit-label="type === 'website' ? $t('tenant.sources.wizard.startCrawl') : $t('tenant.sources.wizard.uploadFile')"
    @close="$emit('close')"
    @back="step--"
    @next="nextStep"
    @submit="submit"
  >

            <!-- Step 0: Pick type -->
            <div v-if="step === 0">
              <p class="step-subtext mb-6">{{ $t('tenant.sources.wizard.stepType') }}</p>
              <div class="grid grid-cols-2 gap-4">
                <button @click="selectType('website')"
                  class="radio-card flex-col items-start gap-3 p-6"
                  :class="{ 'is-selected': type === 'website' }">
                  <div class="type-icon"
                    :class="type === 'website' ? 'type-icon--active' : ''">
                    <font-awesome-icon :icon="['fas', 'globe']" />
                  </div>
                  <div>
                    <p class="font-bold text-foreground text-sm">{{ $t('tenant.sources.wizard.typeWebsite') }}</p>
                    <p class="step-subtext mt-1">{{ $t('tenant.sources.wizard.typeWebsiteDesc') }}</p>
                  </div>
                </button>
                <button @click="selectType('document')"
                  class="radio-card flex-col items-start gap-3 p-6"
                  :class="{ 'is-selected': type === 'document' }">
                  <div class="type-icon"
                    :class="type === 'document' ? 'type-icon--active' : ''">
                    <font-awesome-icon :icon="['fas', 'file-lines']" />
                  </div>
                  <div>
                    <p class="font-bold text-foreground text-sm">{{ $t('tenant.sources.wizard.typeDocument') }}</p>
                    <p class="step-subtext mt-1">{{ $t('tenant.sources.wizard.typeDocumentDesc') }}</p>
                  </div>
                </button>
              </div>
              <div class="info-box" style="margin-top:20px;">
                <font-awesome-icon :icon="['fas', 'circle-info']" class="info-box__icon" />
                <div>
                  <p class="info-box__title">{{ $t('tenant.sources.wizard.infoTitle') }}</p>
                  <p class="step-subtext">
                    {{ type === 'document' ? $t('tenant.sources.wizard.infoDocument') : $t('tenant.sources.wizard.infoWebsite') }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Step 1: Configure -->
            <div v-if="step === 1">
              <!-- Website: address and how much of it -->
              <div v-if="type === 'website'" class="flex flex-col gap-6">
                <Field>
                  <FieldLabel>{{ $t('tenant.sources.wizard.urlLabel') }}</FieldLabel>
                  <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-base-content/30">
                      <font-awesome-icon :icon="['fas', 'link']" />
                    </div>
                    <Input v-model="url" type="text" :placeholder="$t('tenant.sources.wizard.urlPlaceholder')"
                      class="pl-11" :class="{ 'has-error': !isUrlValid && url }" />
                  </div>
                  <p v-if="!isUrlValid && url" class="text-error text-xs px-1 mt-1.5 flex items-center gap-1">
                    <font-awesome-icon :icon="['fas', 'circle-exclamation']" /> {{ $t('tenant.sources.invalidUrl') }}
                  </p>
                </Field>

                <div class="flex flex-col gap-3">
                  <Label class="mb-2">{{ $t('tenant.sources.wizard.scope.question') }}</Label>
                  <button v-for="scope in scopes" :key="scope.single" type="button" @click="singlePageOnly = scope.single"
                    class="radio-card p-4" :class="{ 'is-selected': singlePageOnly === scope.single }">
                    <div class="text-xl mt-0.5"><font-awesome-icon :icon="['fas', scope.icon]" /></div>
                    <div class="flex-1">
                      <p class="step-heading">{{ scope.title }}</p>
                      <p class="step-subtext">{{ scope.desc }}</p>
                    </div>
                    <div class="radio-card__dot"></div>
                  </button>
                </div>
              </div>

              <!-- Document -->
              <div v-if="type === 'document'">
                <label for="wiz-file-upload" class="file-drop" :class="{ 'file-drop--active': selectedFile }">
                  <input id="wiz-file-upload" type="file" @change="handleFileSelect" accept=".pdf,.txt,.csv" class="sr-only" />
                  <div class="file-drop__icon" :class="{ 'file-drop__icon--active': selectedFile }">
                    <font-awesome-icon :icon="selectedFile ? ['fas', 'file-circle-check'] : ['fas', 'file-arrow-up']" />
                  </div>
                  <div class="text-center">
                    <p class="file-drop__name" :class="{ 'file-drop__name--active': selectedFile }">
                      {{ selectedFile ? selectedFile.name : $t('tenant.sources.wizard.chooseFile') }}
                    </p>
                    <p class="step-subtext" style="margin-top:4px;">PDF · TXT · CSV</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Step 2: Options -->
            <div v-if="step === 2 && type === 'website'" class="flex flex-col gap-7">
              <template v-if="!singlePageOnly">
                <section class="flex flex-col gap-3">
                  <p class="step-heading">{{ $t('tenant.sources.wizard.options.title') }}</p>
                  <label v-for="opt in crawlOptions" :key="opt.key" class="option-row">
                    <Checkbox v-model="options[opt.key]" class="mt-0.5" />
                    <span>
                      <span class="step-heading block">{{ $t(`tenant.sources.wizard.options.${opt.key}`) }}</span>
                      <span class="step-subtext block">{{ $t(`tenant.sources.wizard.options.${opt.key}Desc`) }}</span>
                    </span>
                  </label>
                </section>

                <section class="flex flex-col gap-3">
                  <div>
                    <p class="step-heading">{{ $t('tenant.sources.wizard.exclude.title') }}</p>
                    <p class="step-subtext">{{ $t('tenant.sources.wizard.exclude.desc') }}</p>
                  </div>

                  <div v-if="excludedPaths.length > 0" class="flex flex-wrap gap-2">
                    <div v-for="(path, i) in excludedPaths" :key="i" class="path-chip">
                      <span>{{ path }}</span>
                      <button type="button" @click="removeExclusion(i)" class="path-chip__remove">
                        <font-awesome-icon :icon="['fas', 'xmark']" />
                      </button>
                    </div>
                  </div>

                  <div v-if="addingExclusion" class="path-input-row">
                    <div class="relative flex-1">
                      <div v-if="!isHostOrUrl(exclusionDraft)" class="absolute inset-y-0 left-3 flex items-center text-base-content/30 text-xs pointer-events-none">/</div>
                      <input ref="exclusionInput" v-model="exclusionDraft"
                        @keydown.enter.prevent="confirmExclusion"
                        @keydown.escape="addingExclusion = false; exclusionDraft = ''"
                        :placeholder="$t('tenant.sources.wizard.exclude.placeholder')" />
                    </div>
                    <BcButton variant="primary" size="sm" type="button" @click="confirmExclusion" class="rounded-xl px-4">{{ $t('tenant.sources.wizard.exclude.add') }}</BcButton>
                    <BcButton variant="quiet" size="sm" type="button" @click="addingExclusion = false; exclusionDraft = ''" class="rounded-xl">{{ $t('tenant.sources.wizard.exclude.cancel') }}</BcButton>
                  </div>

                  <button v-if="!addingExclusion" type="button" @click="addExclusion" class="add-row">
                    <span class="add-row__icon"><font-awesome-icon :icon="['fas', 'plus']" class="text-xs" /></span>
                    {{ $t('tenant.sources.wizard.exclude.addRow') }}
                  </button>
                </section>
              </template>

              <section class="flex flex-col gap-2">
                <p class="step-heading">{{ $t('tenant.sources.wizard.crawlModeLabel') }}</p>
                <p class="step-subtext">{{ $t('tenant.sources.wizard.crawlModeHint') }}</p>
                <button v-for="mode in crawlModes" :key="mode.value" type="button"
                  @click="crawlMode = mode.value"
                  class="radio-card"
                  :class="{ 'is-selected': crawlMode === mode.value }">
                  <div class="text-xl leading-none mt-0.5 w-6 shrink-0"><font-awesome-icon :icon="['fas', mode.icon]" /></div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-bold text-foreground">{{ mode.label }}</span>
                      <span v-if="mode.badge"
                        class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                        :class="mode.badgeClass">{{ mode.badge }}</span>
                    </div>
                    <p class="step-subtext mt-0.5">{{ mode.desc }}</p>
                  </div>
                  <div class="radio-card__dot"></div>
                </button>
              </section>
            </div>

            <!-- Confirm -->
            <div v-if="step === lastStep" class="confirm-summary">
              <p class="step-subtext mb-6">{{ $t('tenant.sources.wizard.confirmTitle') }}</p>

              <div class="confirm-card">

                <!-- Type -->
                <div class="confirm-item">
                  <span class="confirm-item__icon"><font-awesome-icon :icon="type === 'website' ? ['fas', 'globe'] : ['fas', 'file']" /></span>
                  <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmType') }}</span>
                  <span class="confirm-item__value">{{ type === 'website' ? $t('tenant.sources.wizard.typeWebsite') : $t('tenant.sources.wizard.typeDocument') }}</span>
                </div>

                <template v-if="type === 'website'">
                  <!-- URL -->
                  <div class="confirm-item">
                    <span class="confirm-item__icon"><font-awesome-icon :icon="['fas', 'link']" /></span>
                    <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmUrl') }}</span>
                    <span class="confirm-item__value confirm-item__value--mono">{{ finalUrl }}</span>
                  </div>

                  <!-- Mode -->
                  <div class="confirm-item">
                    <span class="confirm-item__icon"><font-awesome-icon :icon="['fas', 'bolt']" /></span>
                    <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmMode') }}</span>
                    <span class="confirm-item__value">{{ crawlModes.find((m) => m.value === crawlMode)?.label }}</span>
                  </div>

                  <!-- Scope -->
                  <div class="confirm-item">
                    <span class="confirm-item__icon"><font-awesome-icon :icon="['fas', 'sitemap']" /></span>
                    <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmScope') }}</span>
                    <span class="confirm-item__value">{{ singlePageOnly ? $t('tenant.sources.wizard.confirmSinglePage') : $t('tenant.sources.wizard.confirmFullSite') }}</span>
                  </div>

                  <!-- Options -->
                  <div v-if="!singlePageOnly && enabledOptions.length > 0" class="confirm-item">
                    <span class="confirm-item__icon"><font-awesome-icon :icon="['fas', 'sliders']" /></span>
                    <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmOptions') }}</span>
                    <div class="confirm-exclusions">
                      <span v-for="key in enabledOptions" :key="key" class="confirm-exclusion">{{ $t(`tenant.sources.wizard.options.${key}`) }}</span>
                    </div>
                  </div>

                  <!-- Exclusions -->
                  <div v-if="!singlePageOnly && excludedPaths.length > 0" class="confirm-item">
                    <span class="confirm-item__icon"><font-awesome-icon :icon="['fas', 'ban']" /></span>
                    <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmExcluded') }}</span>
                    <div class="confirm-exclusions">
                      <span v-for="(path, i) in excludedPaths" :key="i" class="confirm-exclusion">{{ path }}</span>
                    </div>
                  </div>
                </template>

                <template v-else>
                  <!-- File -->
                  <div class="confirm-item">
                    <span class="confirm-item__icon"><font-awesome-icon :icon="['fas', 'file-arrow-up']" /></span>
                    <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmFile') }}</span>
                    <span class="confirm-item__value confirm-item__value--mono">{{ selectedFile?.name }}</span>
                  </div>
                </template>

              </div>
            </div>
  </WizardPanel>
</template>

<script setup>
import { Checkbox } from '@/components/ui/checkbox';
import { Field, FieldLabel } from '@/components/ui/field';
import { BcButton } from '@/components/ui';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ref, reactive, computed, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import WizardPanel from '../../WizardPanel.vue';
import { useToast } from '../../../composables/useToast';
import { useTenantsStore } from '../../../stores/tenants';
import apiClient from '@/utils/api';

const props = defineProps({ open: { type: Boolean, default: false } });
const emit = defineEmits(['close', 'crawl-started', 'upload-done']);

const { t } = useI18n();
const { addToast } = useToast();
const tenantsStore = useTenantsStore();

const step = ref(0);
const type = ref(null); // 'website' | 'document'

// document: type → upload → confirm; website: type → address → options → confirm
const lastStep = computed(() => (type.value === 'website' ? 3 : 2));

const scopes = computed(() => [
  { single: false, icon: 'globe', title: t('tenant.sources.wizard.scope.fullTitle'), desc: t('tenant.sources.wizard.scope.fullDesc') },
  { single: true,  icon: 'file', title: t('tenant.sources.wizard.singlePageLabel'), desc: t('tenant.sources.wizard.scope.singleDesc') },
]);

const crawlModes = computed(() => [
  { value: 'soup',       icon: 'bolt', label: t('tenant.sources.wizard.modeSoup'),       desc: t('tenant.sources.wizard.modeSoupDesc'),      badge: t('tenant.sources.wizard.modeSoupBadge'),       badgeClass: 'bg-success/15 text-success' },
  { value: 'playwright', icon: 'globe', label: t('tenant.sources.wizard.modePlaywright'), desc: t('tenant.sources.wizard.modePlaywrightDesc'), badge: t('tenant.sources.wizard.modePlaywrightBadge'), badgeClass: 'bg-warning/15 text-warning'  },
]);
const url = ref('');
const crawlMode = ref('soup');
const singlePageOnly = ref(false);
const addingExclusion = ref(false);
const exclusionDraft = ref('');
const exclusionInput = ref(null);
const excludedPaths = ref([]);
// What a whole-site crawl reads; all on by default
const crawlOptions = [{ key: 'useSitemap' }, { key: 'sameLanguage' }, { key: 'skipFunnel' }];
const defaultOptions = () => ({ useSitemap: true, sameLanguage: true, skipFunnel: true });
const options = reactive(defaultOptions());
const enabledOptions = computed(() => crawlOptions.map((o) => o.key).filter((k) => options[k]));
const selectedFile = ref(null);
const submitting = ref(false);

const selectType = (t) => { type.value = t; };

const finalUrl = computed(() => {
  let u = url.value.trim();
  if (u && !u.startsWith('http://') && !u.startsWith('https://')) u = 'https://' + u;
  return u;
});

const isUrlValid = computed(() => {
  if (!url.value) return true;
  try { const u = new URL(finalUrl.value); return u.protocol === 'http:' || u.protocol === 'https:'; } catch { return false; }
});

const canProceed = computed(() => {
  if (step.value === 0) return !!type.value;
  if (step.value === 1 && type.value === 'website') return !!url.value && isUrlValid.value;
  if (step.value === 1 && type.value === 'document') return !!selectedFile.value;
  return true; // options can always be left as they are
});

const nextStep = () => { if (canProceed.value) step.value++; };

const handleFileSelect = (e) => { selectedFile.value = e.target.files[0] || null; };

const addExclusion = async () => {
  addingExclusion.value = true;
  await nextTick();
  exclusionInput.value?.focus();
};
// "shop.example.com" or "https://…" stays as typed; anything else is a path
const isHostOrUrl = (v) => /^https?:\/\//.test(v) || (!v.startsWith('/') && v.split('/')[0].includes('.'));
const confirmExclusion = () => {
  const draft = exclusionDraft.value.trim();
  const val = isHostOrUrl(draft) ? draft : '/' + draft.replace(/^\/+/, '');
  if (val && val !== '/' && !excludedPaths.value.includes(val)) excludedPaths.value.push(val);
  exclusionDraft.value = '';
  addingExclusion.value = false;
};
const removeExclusion = (i) => excludedPaths.value.splice(i, 1);

const reset = () => {
  step.value = 0; type.value = null; url.value = ''; crawlMode.value = 'soup';
  singlePageOnly.value = false; excludedPaths.value = []; Object.assign(options, defaultOptions()); selectedFile.value = null;
  addingExclusion.value = false; exclusionDraft.value = '';
};

const submit = async () => {
  submitting.value = true;
  const tenantId = tenantsStore.currentTenant?.id;
  try {
    if (type.value === 'website') {
      await apiClient.post(`/tenants/${tenantId}/sources/discover`, {
        url: finalUrl.value,
        single_page_only: singlePageOnly.value,
        excluded_urls: singlePageOnly.value ? [] : excludedPaths.value,
        same_language: !singlePageOnly.value && options.sameLanguage,
        use_sitemap: !singlePageOnly.value && options.useSitemap,
        skip_funnel: !singlePageOnly.value && options.skipFunnel,
        crawl_mode: crawlMode.value,
      });
      addToast(t('tenant.sources.actions.crawlStarted'), 'success');
      emit('crawl-started');
    } else {
      const fd = new FormData();
      fd.append('file', selectedFile.value);
      await apiClient.post(`/tenants/${tenantId}/sources/upload`, fd);
      addToast(t('tenant.sources.actions.uploadSuccess'), 'success');
      emit('upload-done');
    }
  } catch (err) {
    addToast(`${t('tenant.sources.actions.crawlFailed')} ${err.response?.data?.error || err.message || ''}`, 'error');
  } finally {
    submitting.value = false;
    reset();
    emit('close');
  }
};
</script>


/* ── Footer ──────────────────────────────────────────────────────── */
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
<style>

/* ── Option rows ─────────────────────────────────────────────────── */
.option-row {
  display: flex; align-items: flex-start; gap: 12px; cursor: pointer;
  padding: 12px 16px; border-radius: var(--radius-md);
  background: var(--surface-2); border: 1px solid var(--surface-3);
}

/* ── Type icons ──────────────────────────────────────────────────── */
.type-icon {
  width: 40px; height: 40px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  background: var(--surface-2);
  color: var(--surface-muted);
  transition: background var(--t-fast), color var(--t-fast);
}
.type-icon--active { background: rgba(10,31,171,0.15); color: var(--brand-indigo); }

/* ── Info box ────────────────────────────────────────────────────── */
.info-box {
  display: flex; gap: 8px; align-items: flex-start;
  padding: 16px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
}
.info-box__icon  { color: var(--brand-indigo); flex-shrink: 0; margin-top: 2px; }
.info-box__title { font-size: 12px; font-weight: 600; color: var(--surface-text); margin-bottom: 4px; }

/* ── Field icon ──────────────────────────────────────────────────── */
.field-icon {
  position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  padding-left: 16px; pointer-events: none; color: var(--surface-muted);
}

/* ── File drop zone ──────────────────────────────────────────────── */
.file-drop {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 16px; padding: 36px 20px;
  border-radius: var(--radius-lg);
  border: 1.5px dashed var(--surface-3);
  cursor: pointer;
  transition: border-color var(--t-fast), background var(--t-fast);
}
.file-drop:hover       { border-color: var(--brand-indigo); background: rgba(10,31,171,0.04); }
.file-drop--active     { border-color: var(--brand-indigo); background: rgba(10,31,171,0.06); }
.file-drop__icon {
  width: 52px; height: 52px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; background: var(--surface-2); color: var(--surface-muted);
  transition: background var(--t-fast), color var(--t-fast);
}
.file-drop:hover .file-drop__icon,
.file-drop__icon--active { background: rgba(10,31,171,0.15); color: var(--brand-indigo); }
.file-drop__name        { font-size: 14px; font-weight: 600; color: var(--surface-muted); }
.file-drop__name--active { color: var(--brand-indigo); }
</style>

