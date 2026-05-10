<template>
  <Teleport to="body">
    <Transition name="slide-over">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')"></div>

        <div class="wizard-panel">

          <!-- Header -->
          <div class="wizard-header">
            <div>
              <h2 class="wizard-title">{{ $t('tenant.sources.wizard.addKnowledge') }}</h2>
              <div class="wizard-progress">
                <div v-for="i in lastStep + 1" :key="i"
                  class="wizard-progress__dot"
                  :class="{ 'is-active': i - 1 === step, 'is-done': i - 1 < step }"></div>
              </div>
            </div>
            <button @click="$emit('close')" class="wizard-close">
              <font-awesome-icon :icon="['fas', 'xmark']" />
            </button>
          </div>

          <!-- Step content -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">

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
                    <p class="font-bold text-white text-sm">{{ $t('tenant.sources.wizard.typeWebsite') }}</p>
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
                    <p class="font-bold text-white text-sm">{{ $t('tenant.sources.wizard.typeDocument') }}</p>
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
              <!-- Website -->
              <div v-if="type === 'website'" class="space-y-6">
                <div>
                  <label class="field-label">{{ $t('tenant.sources.wizard.crawlModeLabel') }}</label>
                  <div class="space-y-2">
                    <button v-for="mode in crawlModes" :key="mode.value" type="button"
                      @click="crawlMode = mode.value"
                      class="radio-card"
                      :class="{ 'is-selected': crawlMode === mode.value }">
                      <div class="text-xl leading-none mt-0.5 w-6 flex-shrink-0">{{ mode.emoji }}</div>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="text-sm font-bold text-white">{{ mode.label }}</span>
                          <span v-if="mode.badge"
                            class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                            :class="mode.badgeClass">{{ mode.badge }}</span>
                        </div>
                        <p class="step-subtext mt-0.5">{{ mode.desc }}</p>
                      </div>
                      <div class="radio-card__dot"></div>
                    </button>
                  </div>
                </div>

                <div>
                  <label class="field-label">{{ $t('tenant.sources.wizard.urlLabel') }}</label>
                  <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-base-content/30">
                      <font-awesome-icon :icon="['fas', 'link']" />
                    </div>
                    <input v-model="url" type="text" :placeholder="$t('tenant.sources.wizard.urlPlaceholder')"
                      class="field-input pl-11" :class="{ 'has-error': !isUrlValid && url }" />
                  </div>
                  <p v-if="!isUrlValid && url" class="text-error text-xs px-1 mt-1.5 flex items-center gap-1">
                    <font-awesome-icon :icon="['fas', 'circle-exclamation']" /> {{ $t('tenant.sources.invalidUrl') }}
                  </p>
                </div>
              </div>

              <!-- Document -->
              <div v-if="type === 'document'">
                <label for="wiz-file-upload" class="file-drop" :class="{ 'file-drop--active': selectedFile }">
                  <input id="wiz-file-upload" type="file" @change="handleFileSelect" accept=".pdf,.txt,.csv" class="sr-only" />
                  <div class="file-drop__icon" :class="{ 'file-drop__icon--active': selectedFile }">
                    <font-awesome-icon :icon="selectedFile ? ['fas', 'file-check'] : ['fas', 'file-arrow-up']" />
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

            <!-- Step 2: Scope -->
            <div v-if="step === 2 && type === 'website'" class="space-y-3">
              <p class="step-subtext mb-2">How much of this site should we index?</p>
              <button type="button" @click="singlePageOnly = false"
                class="radio-card p-5"
                :class="{ 'is-selected': !singlePageOnly }">
                <div class="text-xl mt-0.5">🌐</div>
                <div class="flex-1">
                  <p class="step-heading">Full site crawl</p>
                  <p class="step-subtext">Follow internal links and index all reachable pages</p>
                </div>
                <div class="radio-card__dot"></div>
              </button>
              <button type="button" @click="singlePageOnly = true"
                class="radio-card p-5"
                :class="{ 'is-selected': singlePageOnly }">
                <div class="text-xl mt-0.5">📄</div>
                <div class="flex-1">
                  <p class="step-heading">{{ $t('tenant.sources.wizard.singlePageLabel') }}</p>
                  <p class="step-subtext">Only index this exact URL — skip all internal links</p>
                </div>
                <div class="radio-card__dot"></div>
              </button>
            </div>

            <!-- Step 3: Exclusions -->
            <div v-if="step === 3 && type === 'website' && !singlePageOnly" class="space-y-5">
              <div>
                <p class="step-heading">Exclude paths &amp; subdomains</p>
                <p class="step-subtext">
                  These paths or subdomains will be skipped entirely during crawling.
                  Useful for login pages, dashboards, staging subdomains, or any section you don't want indexed.
                </p>
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
                  <div v-if="!exclusionDraft.startsWith('http')" class="absolute inset-y-0 left-3 flex items-center text-base-content/30 text-xs pointer-events-none">/</div>
                  <input ref="exclusionInput" v-model="exclusionDraft"
                    @keydown.enter.prevent="confirmExclusion"
                    @keydown.escape="addingExclusion = false; exclusionDraft = ''"
                    placeholder="login  or  shop.example.com" />
                </div>
                <button type="button" @click="confirmExclusion" class="btn btn-sm btn-primary rounded-xl px-4">Add</button>
                <button type="button" @click="addingExclusion = false; exclusionDraft = ''" class="btn btn-sm btn-ghost rounded-xl">Cancel</button>
              </div>

              <button v-if="!addingExclusion" type="button" @click="addExclusion" class="add-row">
                <span class="add-row__icon"><font-awesome-icon :icon="['fas', 'plus']" class="text-xs" /></span>
                Add a path or subdomain
              </button>

              <p v-if="excludedPaths.length === 0 && !addingExclusion" class="step-subtext italic">
                No exclusions added — you can skip this step.
              </p>
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
                    <span class="confirm-item__value">{{ crawlMode }}</span>
                  </div>

                  <!-- Scope -->
                  <div class="confirm-item">
                    <span class="confirm-item__icon"><font-awesome-icon :icon="['fas', 'sitemap']" /></span>
                    <span class="confirm-item__label">{{ $t('tenant.sources.wizard.confirmScope') }}</span>
                    <span class="confirm-item__value">{{ singlePageOnly ? $t('tenant.sources.wizard.confirmSinglePage') : $t('tenant.sources.wizard.confirmFullSite') }}</span>
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
          </div>

          <!-- Footer -->
          <div class="wizard-footer">
            <button v-if="step > 0" @click="step--" class="wiz-btn wiz-btn--ghost">
              <font-awesome-icon :icon="['fas', 'arrow-left']" /> {{ $t('tenant.sources.wizard.back') }}
            </button>
            <button v-if="step < lastStep" @click="nextStep" :disabled="!canProceed" class="wiz-btn wiz-btn--primary">
              {{ $t('tenant.sources.wizard.next') }} <font-awesome-icon :icon="['fas', 'arrow-right']" />
            </button>
            <button v-if="step === lastStep" @click="submit" :disabled="submitting" class="wiz-btn wiz-btn--primary">
              <font-awesome-icon v-if="submitting" :icon="['fas', 'spinner']" class="spin" />
              {{ type === 'website' ? $t('tenant.sources.wizard.startCrawl') : $t('tenant.sources.wizard.uploadFile') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
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

// lastStep: 1 (document) | 3 (website single page) | 4 (website full site)
const lastStep = computed(() => {
  if (type.value !== 'website') return 2; // type → upload → confirm
  return singlePageOnly.value ? 3 : 4;    // type → configure → scope → [exclusions] → confirm
});

const crawlModes = computed(() => [
  { value: 'soup',       emoji: '⚡', label: t('tenant.sources.wizard.modeSoup'),       desc: t('tenant.sources.wizard.modeSoupDesc'),      badge: 'Fastest',  badgeClass: 'bg-success/15 text-success' },
  { value: 'playwright', emoji: '🌐', label: t('tenant.sources.wizard.modePlaywright'), desc: t('tenant.sources.wizard.modePlaywrightDesc'), badge: 'JS sites', badgeClass: 'bg-warning/15 text-warning'  },
]);
const url = ref('');
const crawlMode = ref('soup');
const singlePageOnly = ref(false);
const addingExclusion = ref(false);
const exclusionDraft = ref('');
const exclusionInput = ref(null);
const excludedPaths = ref([]);
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
  return true; // scope and exclusions steps are always skippable
});

const nextStep = () => { if (canProceed.value) step.value++; };

const handleFileSelect = (e) => { selectedFile.value = e.target.files[0] || null; };

const addExclusion = async () => {
  addingExclusion.value = true;
  await nextTick();
  exclusionInput.value?.focus();
};
const confirmExclusion = () => {
  const val = ('/' + exclusionDraft.value.replace(/^\/+/, '')).trim();
  if (val && val !== '/' && !excludedPaths.value.includes(val)) excludedPaths.value.push(val);
  exclusionDraft.value = '';
  addingExclusion.value = false;
};
const removeExclusion = (i) => excludedPaths.value.splice(i, 1);

const reset = () => {
  step.value = 0; type.value = null; url.value = ''; crawlMode.value = 'soup';
  singlePageOnly.value = false; excludedPaths.value = []; selectedFile.value = null;
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

<style scoped>
/* ── Slide transition ─────────────────────────────────────────────── */
.slide-over-enter-active, .slide-over-leave-active { transition: opacity 0.25s ease; }
.slide-over-enter-active .wizard-panel, .slide-over-leave-active .wizard-panel { transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); }
.slide-over-enter-from { opacity: 0; }
.slide-over-enter-from .wizard-panel { transform: translateX(100%); }
.slide-over-leave-to { opacity: 0; }
.slide-over-leave-to .wizard-panel { transform: translateX(100%); }

/* ── Panel shell ─────────────────────────────────────────────────── */
.wizard-panel {
  position: relative;
  width: 100%;
  max-width: 420px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-1);
  border-left: 1px solid var(--surface-3);
  box-shadow: -8px 0 40px rgba(0,0,0,0.4);
}

/* ── Header ──────────────────────────────────────────────────────── */
.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--surface-3);
}

.wizard-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--surface-heading);
}

.wizard-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  color: var(--surface-muted);
  cursor: pointer;
  transition: color var(--t-fast), border-color var(--t-fast);
}
.wizard-close:hover { color: var(--surface-text); border-color: var(--surface-muted); }

/* ── Type icons ──────────────────────────────────────────────────── */
.type-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: var(--surface-2);
  color: var(--surface-muted);
  transition: background var(--t-fast), color var(--t-fast);
}
.type-icon--active {
  background: rgba(10, 31, 171, 0.15);
  color: var(--brand-indigo);
}

/* ── Info box ─────────────────────────────────────────────────────── */
.info-box {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
}
.info-box__icon { color: var(--brand-indigo); flex-shrink: 0; margin-top: 2px; }
.info-box__title { font-size: 12px; font-weight: 600; color: var(--surface-text); margin-bottom: 4px; }

/* ── Field position icon ─────────────────────────────────────────── */
.field-icon {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  padding-left: 14px;
  pointer-events: none;
  color: var(--surface-muted);
}

/* ── File drop zone ──────────────────────────────────────────────── */
.file-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 36px 20px;
  border-radius: var(--radius-lg);
  border: 1.5px dashed var(--surface-3);
  cursor: pointer;
  transition: border-color var(--t-fast), background var(--t-fast);
}
.file-drop:hover { border-color: var(--brand-indigo); background: rgba(10,31,171,0.04); }
.file-drop--active { border-color: var(--brand-indigo); background: rgba(10,31,171,0.06); }

.file-drop__icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: var(--surface-2);
  color: var(--surface-muted);
  transition: background var(--t-fast), color var(--t-fast);
}
.file-drop:hover .file-drop__icon,
.file-drop__icon--active { background: rgba(10,31,171,0.15); color: var(--brand-indigo); }

.file-drop__name { font-size: 13px; font-weight: 600; color: var(--surface-muted); }
.file-drop__name--active { color: var(--brand-indigo); }

/* ── Footer ──────────────────────────────────────────────────────── */
.wizard-footer {
  display: flex;
  gap: 10px;
  padding: 20px 24px;
  border-top: 1px solid var(--surface-3);
}

.wiz-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: opacity var(--t-fast), background var(--t-fast);
}
.wiz-btn--primary { background: var(--gradient-brand); color: white; }
.wiz-btn--primary:hover:not(:disabled) { opacity: 0.9; }
.wiz-btn--primary:disabled { opacity: 0.4; cursor: not-allowed; }
.wiz-btn--ghost { background: var(--surface-2); border: 1px solid var(--surface-3); color: var(--surface-text); }
.wiz-btn--ghost:hover { border-color: var(--surface-muted); }

.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>

