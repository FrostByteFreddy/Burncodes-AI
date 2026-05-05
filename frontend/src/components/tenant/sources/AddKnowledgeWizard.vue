<template>
  <Teleport to="body">
    <Transition name="slide-over">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')"></div>

        <!-- Panel -->
        <div class="relative w-full max-w-md bg-base-100 h-full flex flex-col shadow-2xl">
          <!-- Header -->
          <div class="flex items-center justify-between p-6 border-b border-base-200/50">
            <div>
              <h2 class="text-xl font-bold text-base-content">{{ $t('tenant.sources.wizard.addKnowledge') }}</h2>
              <div class="flex items-center gap-2 mt-2">
                <div v-for="(s, i) in steps" :key="i"
                  class="h-1 rounded-full transition-all duration-300"
                  :class="[i <= step ? 'bg-primary' : 'bg-base-300', i === step ? 'w-8' : 'w-4']"></div>
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
              <p class="text-sm text-base-content/60 mb-6">{{ $t('tenant.sources.wizard.stepType') }}</p>
              <div class="grid grid-cols-2 gap-4">
                <button @click="selectType('website')"
                  class="group p-6 rounded-2xl border-2 transition-all duration-200 text-left"
                  :class="type === 'website' ? 'border-primary bg-primary/5' : 'border-base-200 hover:border-primary/40 bg-base-100'">
                  <div class="w-10 h-10 rounded-xl mb-4 flex items-center justify-center text-xl"
                    :class="type === 'website' ? 'bg-primary/20 text-primary' : 'bg-base-200 text-base-content/50 group-hover:bg-primary/10 group-hover:text-primary'">
                    <font-awesome-icon :icon="['fas', 'globe']" />
                  </div>
                  <p class="font-bold text-base-content text-sm">{{ $t('tenant.sources.wizard.typeWebsite') }}</p>
                  <p class="text-xs text-base-content/50 mt-1 leading-relaxed">{{ $t('tenant.sources.wizard.typeWebsiteDesc') }}</p>
                </button>
                <button @click="selectType('document')"
                  class="group p-6 rounded-2xl border-2 transition-all duration-200 text-left"
                  :class="type === 'document' ? 'border-secondary bg-secondary/5' : 'border-base-200 hover:border-secondary/40 bg-base-100'">
                  <div class="w-10 h-10 rounded-xl mb-4 flex items-center justify-center text-xl"
                    :class="type === 'document' ? 'bg-secondary/20 text-secondary' : 'bg-base-200 text-base-content/50 group-hover:bg-secondary/10 group-hover:text-secondary'">
                    <font-awesome-icon :icon="['fas', 'file-lines']" />
                  </div>
                  <p class="font-bold text-base-content text-sm">{{ $t('tenant.sources.wizard.typeDocument') }}</p>
                  <p class="text-xs text-base-content/50 mt-1 leading-relaxed">{{ $t('tenant.sources.wizard.typeDocumentDesc') }}</p>
                </button>
              </div>

              <!-- Info box -->
              <div class="mt-6 bg-base-200/50 rounded-2xl p-4 border border-base-200">
                <p class="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-2 flex items-center gap-2">
                  <font-awesome-icon :icon="['fas', 'circle-info']" /> {{ $t('tenant.sources.wizard.infoTitle') }}
                </p>
                <p class="text-xs text-base-content/60 leading-relaxed">
                  {{ type === 'document' ? $t('tenant.sources.wizard.infoDocument') : $t('tenant.sources.wizard.infoWebsite') }}
                </p>
              </div>
            </div>

            <!-- Step 1: Configure -->
            <div v-if="step === 1">
              <!-- Website form -->
              <div v-if="type === 'website'" class="space-y-6">

                <!-- URL -->
                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-base-content/50 mb-2">{{ $t('tenant.sources.wizard.urlLabel') }}</label>
                  <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-base-content/30">
                      <font-awesome-icon :icon="['fas', 'link']" />
                    </div>
                    <input v-model="url" type="text" :placeholder="$t('tenant.sources.wizard.urlPlaceholder')"
                      class="input w-full bg-base-200/60 border-2 border-transparent focus:border-primary focus:bg-base-100 transition-all pl-11 rounded-2xl text-sm font-medium h-12"
                      :class="{ 'border-error bg-error/5 focus:border-error': !isUrlValid && url }" />
                  </div>
                  <p v-if="!isUrlValid && url" class="text-error text-xs px-1 mt-1.5 flex items-center gap-1">
                    <font-awesome-icon :icon="['fas', 'circle-exclamation']" /> {{ $t('tenant.sources.invalidUrl') }}
                  </p>
                </div>

                <!-- Crawl Mode cards -->
                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-base-content/50 mb-3">{{ $t('tenant.sources.wizard.crawlModeLabel') }}</label>
                  <div class="space-y-2">
                    <button v-for="mode in crawlModes" :key="mode.value" type="button"
                      @click="crawlMode = mode.value"
                      class="w-full flex items-start gap-4 p-4 rounded-2xl border-2 transition-all duration-150 text-left"
                      :class="crawlMode === mode.value
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-base-200 bg-base-100 hover:border-base-300'">
                      <div class="text-xl leading-none mt-0.5 w-6 flex-shrink-0">{{ mode.emoji }}</div>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="text-sm font-bold" :class="crawlMode === mode.value ? 'text-primary' : 'text-base-content'">{{ mode.label }}</span>
                          <span v-if="mode.badge" class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                            :class="mode.badgeClass">{{ mode.badge }}</span>
                        </div>
                        <p class="text-xs text-base-content/50 mt-0.5 leading-relaxed">{{ mode.desc }}</p>
                      </div>
                      <div class="w-4 h-4 rounded-full border-2 flex-shrink-0 mt-1 transition-all flex items-center justify-center"
                        :class="crawlMode === mode.value ? 'border-primary bg-primary' : 'border-base-300'">
                        <div v-if="crawlMode === mode.value" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                      </div>
                    </button>
                  </div>
                </div>

                <!-- Scope -->
                <div class="rounded-2xl border border-base-200 overflow-hidden">
                  <label for="wiz_single"
                    class="flex items-center gap-3 p-4 cursor-pointer hover:bg-base-200/40 transition-colors select-none"
                    :class="singlePageOnly ? 'bg-base-200/30' : ''">
                    <input type="checkbox" v-model="singlePageOnly" id="wiz_single"
                      class="checkbox checkbox-sm checkbox-primary rounded" />
                    <div class="flex-1">
                      <p class="text-sm font-semibold text-base-content">{{ $t('tenant.sources.wizard.singlePageLabel') }}</p>
                      <p class="text-xs text-base-content/40 mt-0.5">Only index this exact URL — skip all internal links</p>
                    </div>
                  </label>
                </div>

                <!-- Exclusions — only shown when crawling full site -->
                <Transition name="fade-down">
                  <div v-if="!singlePageOnly" class="space-y-3">
                    <div class="flex items-center justify-between">
                      <div>
                        <p class="text-xs font-bold uppercase tracking-wider text-base-content/50">Excluded paths</p>
                        <p class="text-xs text-base-content/40 mt-0.5">These paths will be skipped — useful for login pages, dashboards, or private sections.</p>
                      </div>
                      <button type="button" @click="addExclusion"
                        class="btn btn-ghost btn-sm btn-circle border border-base-200 hover:border-primary/50 hover:bg-primary/5 hover:text-primary">
                        <font-awesome-icon :icon="['fas', 'plus']" />
                      </button>
                    </div>

                    <!-- chips -->
                    <div v-if="excludedPaths.length > 0" class="flex flex-wrap gap-2">
                      <div v-for="(path, i) in excludedPaths" :key="i"
                        class="flex items-center gap-1.5 bg-base-200 text-base-content/70 text-xs font-mono px-3 py-1.5 rounded-xl border border-base-200 group">
                        <span>{{ path }}</span>
                        <button type="button" @click="removeExclusion(i)"
                          class="text-base-content/30 hover:text-error transition-colors ml-1">
                          <font-awesome-icon :icon="['fas', 'xmark']" />
                        </button>
                      </div>
                    </div>

                    <!-- inline path input -->
                    <div v-if="addingExclusion" class="flex gap-2">
                      <div class="relative flex-1">
                        <div class="absolute inset-y-0 left-3 flex items-center text-base-content/30 text-xs pointer-events-none">/</div>
                        <input ref="exclusionInput" v-model="exclusionDraft"
                          @keydown.enter.prevent="confirmExclusion"
                          @keydown.escape="addingExclusion = false; exclusionDraft = ''"
                          placeholder="login"
                          class="input input-sm w-full bg-base-200 border-2 border-primary/40 focus:border-primary rounded-xl pl-6 font-mono text-sm" />
                      </div>
                      <button type="button" @click="confirmExclusion" class="btn btn-sm btn-primary rounded-xl px-4">Add</button>
                      <button type="button" @click="addingExclusion = false; exclusionDraft = ''" class="btn btn-sm btn-ghost rounded-xl">Cancel</button>
                    </div>

                    <p v-if="excludedPaths.length === 0 && !addingExclusion"
                      class="text-xs text-base-content/30 italic">No exclusions yet — click + to add a path.</p>
                  </div>
                </Transition>
              </div>

              <!-- Document form -->
              <div v-if="type === 'document'" class="space-y-5">
                <label for="wiz-file-upload"
                  class="flex flex-col items-center justify-center gap-4 p-10 rounded-3xl border-2 border-dashed transition-all duration-200 cursor-pointer group"
                  :class="selectedFile ? 'border-primary bg-primary/5' : 'border-base-300 hover:border-primary/50 bg-base-50'">
                  <input id="wiz-file-upload" type="file" @change="handleFileSelect" accept=".pdf,.txt,.csv" class="sr-only" />
                  <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl transition-colors"
                    :class="selectedFile ? 'bg-primary/20 text-primary' : 'bg-base-200 text-base-content/30 group-hover:bg-primary/10 group-hover:text-primary'">
                    <font-awesome-icon :icon="selectedFile ? ['fas', 'file-check'] : ['fas', 'file-arrow-up']" />
                  </div>
                  <div class="text-center">
                    <p class="text-sm font-bold" :class="selectedFile ? 'text-primary' : 'text-base-content/70'">
                      {{ selectedFile ? selectedFile.name : 'Click to choose a file' }}
                    </p>
                    <p class="text-xs text-base-content/40 mt-1">PDF · TXT · CSV</p>
                  </div>
                </label>
              </div>
            </div>


            <!-- Step 2: Confirm -->
            <div v-if="step === 2">
              <p class="text-sm text-base-content/60 mb-6">{{ $t('tenant.sources.wizard.confirmTitle') }}</p>
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

          <!-- Footer actions -->
          <div class="p-6 border-t border-base-200/50 flex gap-3">
            <button v-if="step > 0" @click="step--" class="btn btn-ghost flex-1">
              <font-awesome-icon :icon="['fas', 'arrow-left']" class="mr-2" />{{ $t('tenant.sources.wizard.back') }}
            </button>
            <button v-if="step < 2" @click="nextStep" :disabled="!canProceed" class="btn btn-primary flex-1">
              {{ $t('tenant.sources.wizard.next') }}<font-awesome-icon :icon="['fas', 'arrow-right']" class="ml-2" />
            </button>
            <button v-if="step === 2" @click="submit" :disabled="submitting" class="btn btn-primary flex-1">
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

const steps = [0, 1, 2];
const step = ref(0);
const type = ref(null);        // 'website' | 'document'

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
  return true;
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
