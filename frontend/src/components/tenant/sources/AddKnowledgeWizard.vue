<template>
  <Teleport to="body">
    <Transition name="slide-over">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')"></div>

        <div class="relative w-full max-w-md bg-base-100 h-full flex flex-col shadow-2xl">

          <!-- Header -->
          <div class="flex items-center justify-between p-6 border-b border-base-200/50">
            <div>
              <h2 class="text-xl font-bold text-base-content">{{ $t('tenant.sources.wizard.addKnowledge') }}</h2>
              <div class="flex items-center gap-2 mt-2">
                <div v-for="i in lastStep + 1" :key="i"
                  class="h-1 rounded-full transition-all duration-300"
                  :class="[i - 1 <= step ? 'bg-primary' : 'bg-base-300', i - 1 === step ? 'w-8' : 'w-4']"></div>
              </div>
            </div>
            <button @click="$emit('close')" class="btn btn-ghost btn-circle btn-sm">
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
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                    :class="type === 'website' ? 'bg-primary/20 text-primary' : 'bg-base-200 text-base-content/50'">
                    <font-awesome-icon :icon="['fas', 'globe']" />
                  </div>
                  <div>
                    <p class="font-bold text-base-content text-sm">{{ $t('tenant.sources.wizard.typeWebsite') }}</p>
                    <p class="step-subtext mt-1">{{ $t('tenant.sources.wizard.typeWebsiteDesc') }}</p>
                  </div>
                </button>
                <button @click="selectType('document')"
                  class="radio-card flex-col items-start gap-3 p-6"
                  :class="{ 'is-selected': type === 'document' }">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                    :class="type === 'document' ? 'bg-secondary/20 text-secondary' : 'bg-base-200 text-base-content/50'">
                    <font-awesome-icon :icon="['fas', 'file-lines']" />
                  </div>
                  <div>
                    <p class="font-bold text-base-content text-sm">{{ $t('tenant.sources.wizard.typeDocument') }}</p>
                    <p class="step-subtext mt-1">{{ $t('tenant.sources.wizard.typeDocumentDesc') }}</p>
                  </div>
                </button>
              </div>
              <div class="mt-6 bg-base-200/50 rounded-2xl p-4 border border-base-200">
                <p class="field-label mb-2 flex items-center gap-2 normal-case tracking-normal">
                  <font-awesome-icon :icon="['fas', 'circle-info']" /> {{ $t('tenant.sources.wizard.infoTitle') }}
                </p>
                <p class="step-subtext">
                  {{ type === 'document' ? $t('tenant.sources.wizard.infoDocument') : $t('tenant.sources.wizard.infoWebsite') }}
                </p>
              </div>
            </div>

            <!-- Step 1: Configure -->
            <div v-if="step === 1">
              <!-- Website -->
              <div v-if="type === 'website'" class="space-y-6">
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
                          <span class="text-sm font-bold"
                            :class="crawlMode === mode.value ? 'text-primary' : 'text-base-content'">{{ mode.label }}</span>
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
              </div>

              <!-- Document -->
              <div v-if="type === 'document'">
                <label for="wiz-file-upload"
                  class="flex flex-col items-center justify-center gap-4 p-10 rounded-3xl border-2 border-dashed transition-all duration-200 cursor-pointer group"
                  :class="selectedFile ? 'border-primary bg-primary/5' : 'border-base-300 hover:border-primary/50'">
                  <input id="wiz-file-upload" type="file" @change="handleFileSelect" accept=".pdf,.txt,.csv" class="sr-only" />
                  <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl transition-colors"
                    :class="selectedFile ? 'bg-primary/20 text-primary' : 'bg-base-200 text-base-content/30 group-hover:bg-primary/10 group-hover:text-primary'">
                    <font-awesome-icon :icon="selectedFile ? ['fas', 'file-check'] : ['fas', 'file-arrow-up']" />
                  </div>
                  <div class="text-center">
                    <p class="text-sm font-bold" :class="selectedFile ? 'text-primary' : 'text-base-content/70'">
                      {{ selectedFile ? selectedFile.name : 'Click to choose a file' }}
                    </p>
                    <p class="step-subtext mt-1">PDF · TXT · CSV</p>
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
                <p class="step-heading">Exclude paths</p>
                <p class="step-subtext">
                  These paths will be skipped entirely during crawling.
                  Useful for login pages, dashboards, or sections you don't want indexed.
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
                  <div class="absolute inset-y-0 left-3 flex items-center text-base-content/30 text-xs pointer-events-none">/</div>
                  <input ref="exclusionInput" v-model="exclusionDraft"
                    @keydown.enter.prevent="confirmExclusion"
                    @keydown.escape="addingExclusion = false; exclusionDraft = ''"
                    placeholder="login" />
                </div>
                <button type="button" @click="confirmExclusion" class="btn btn-sm btn-primary rounded-xl px-4">Add</button>
                <button type="button" @click="addingExclusion = false; exclusionDraft = ''" class="btn btn-sm btn-ghost rounded-xl">Cancel</button>
              </div>

              <button v-if="!addingExclusion" type="button" @click="addExclusion" class="add-row">
                <span class="add-row__icon"><font-awesome-icon :icon="['fas', 'plus']" class="text-xs" /></span>
                Add a path
              </button>

              <p v-if="excludedPaths.length === 0 && !addingExclusion" class="step-subtext italic">
                No exclusions added — you can skip this step.
              </p>
            </div>

            <!-- Confirm -->
            <div v-if="step === lastStep">
              <p class="step-subtext mb-6">{{ $t('tenant.sources.wizard.confirmTitle') }}</p>
              <div class="bg-base-200/50 rounded-2xl p-5 space-y-3 border border-base-200">
                <div class="flex justify-between text-sm">
                  <span class="text-base-content/50 font-medium">{{ $t('tenant.sources.wizard.confirmType') }}</span>
                  <span class="font-bold text-base-content capitalize">{{ type === 'website' ? $t('tenant.sources.wizard.typeWebsite') : $t('tenant.sources.wizard.typeDocument') }}</span>
                </div>
                <template v-if="type === 'website'">
                  <div class="flex justify-between text-sm">
                    <span class="text-base-content/50 font-medium">{{ $t('tenant.sources.wizard.confirmUrl') }}</span>
                    <span class="font-bold text-base-content truncate max-w-[200px]">{{ finalUrl }}</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-base-content/50 font-medium">{{ $t('tenant.sources.wizard.confirmMode') }}</span>
                    <span class="font-bold text-base-content">{{ crawlMode }}</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-base-content/50 font-medium">Scope</span>
                    <span class="font-bold text-base-content">{{ singlePageOnly ? $t('tenant.sources.wizard.confirmSinglePage') : $t('tenant.sources.wizard.confirmFullSite') }}</span>
                  </div>
                  <div v-if="!singlePageOnly && excludedPaths.length > 0" class="flex justify-between text-sm">
                    <span class="text-base-content/50 font-medium">Excluded</span>
                    <span class="font-bold text-base-content font-mono text-right">{{ excludedPaths.join(', ') }}</span>
                  </div>
                </template>
                <template v-else>
                  <div class="flex justify-between text-sm">
                    <span class="text-base-content/50 font-medium">{{ $t('tenant.sources.wizard.confirmFile') }}</span>
                    <span class="font-bold text-base-content truncate max-w-[200px]">{{ selectedFile?.name }}</span>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="p-6 border-t border-base-200/50 flex gap-3">
            <button v-if="step > 0" @click="step--" class="btn btn-ghost flex-1">
              <font-awesome-icon :icon="['fas', 'arrow-left']" class="mr-2" />{{ $t('tenant.sources.wizard.back') }}
            </button>
            <button v-if="step < lastStep" @click="nextStep" :disabled="!canProceed" class="btn btn-primary flex-1">
              {{ $t('tenant.sources.wizard.next') }}<font-awesome-icon :icon="['fas', 'arrow-right']" class="ml-2" />
            </button>
            <button v-if="step === lastStep" @click="submit" :disabled="submitting" class="btn btn-primary flex-1">
              <font-awesome-icon v-if="submitting" :icon="['fas', 'spinner']" class="animate-spin mr-2" />
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
  { value: 'soup',          emoji: '⚡', label: t('tenant.sources.wizard.modeSoup'),      desc: t('tenant.sources.wizard.modeSoupDesc'),       badge: 'Fastest', badgeClass: 'bg-success/15 text-success' },
  { value: 'playwright',    emoji: '🌐', label: t('tenant.sources.wizard.modePlaywright'), desc: t('tenant.sources.wizard.modePlaywrightDesc'),  badge: 'JS sites', badgeClass: 'bg-warning/15 text-warning' },
  { value: 'playwright_llm',emoji: '🧠', label: t('tenant.sources.wizard.modeLLM'),        desc: t('tenant.sources.wizard.modeLLMDesc'),         badge: 'Best quality', badgeClass: 'bg-primary/15 text-primary' },
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
    reset();
    emit('close');
  } catch (err) {
    addToast(`${t('tenant.sources.actions.crawlFailed')} ${err.response?.data?.error || ''}`, 'error');
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.slide-over-enter-active, .slide-over-leave-active { transition: opacity 0.25s ease; }
.slide-over-enter-active .relative, .slide-over-leave-active .relative { transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); }
.slide-over-enter-from { opacity: 0; }
.slide-over-enter-from .relative { transform: translateX(100%); }
.slide-over-leave-to { opacity: 0; }
.slide-over-leave-to .relative { transform: translateX(100%); }

.fade-down-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-down-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.fade-down-enter-from { opacity: 0; transform: translateY(-6px); }
.fade-down-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
