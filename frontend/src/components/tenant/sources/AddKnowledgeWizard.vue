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
              <div v-if="type === 'website'" class="space-y-5">
                <div>
                  <label class="block text-sm font-medium text-base-content mb-1">{{ $t('tenant.sources.wizard.urlLabel') }}</label>
                  <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-base-content/40">
                      <font-awesome-icon :icon="['fas', 'link']" />
                    </div>
                    <input v-model="url" type="text" :placeholder="$t('tenant.sources.wizard.urlPlaceholder')"
                      class="input w-full bg-base-200/50 border-transparent focus:border-primary focus:bg-base-100 transition-colors pl-12 rounded-2xl text-sm font-medium"
                      :class="{ 'border-error bg-error/5 focus:border-error': !isUrlValid && url }" />
                  </div>
                  <p v-if="!isUrlValid && url" class="text-error text-xs px-2 mt-1">{{ $t('tenant.sources.invalidUrl') }}</p>
                </div>

                <!-- Crawl Mode -->
                <div>
                  <label class="block text-sm font-medium text-base-content mb-1">{{ $t('tenant.sources.wizard.crawlModeLabel') }}</label>
                  <p class="text-xs text-base-content/50 mb-2">{{ $t('tenant.sources.wizard.crawlModeHint') }}</p>
                  <select v-model="crawlMode" class="select select-bordered w-full rounded-2xl bg-base-200 border-transparent focus:border-primary">
                    <option value="soup">⚡ {{ $t('tenant.sources.wizard.modeSoup') }}</option>
                    <option value="playwright">🌐 {{ $t('tenant.sources.wizard.modePlaywright') }}</option>
                    <option value="playwright_llm">🧠 {{ $t('tenant.sources.wizard.modeLLM') }}</option>
                  </select>
                  <p class="text-xs text-base-content/40 mt-2 leading-relaxed">
                    <span v-if="crawlMode === 'soup'">{{ $t('tenant.sources.wizard.modeSoupDesc') }}</span>
                    <span v-else-if="crawlMode === 'playwright'">{{ $t('tenant.sources.wizard.modePlaywrightDesc') }}</span>
                    <span v-else>{{ $t('tenant.sources.wizard.modeLLMDesc') }}</span>
                  </p>
                </div>

                <div class="bg-base-200/30 p-4 rounded-2xl space-y-3">
                  <div class="flex items-center">
                    <input type="checkbox" v-model="singlePageOnly" class="checkbox checkbox-sm checkbox-primary rounded" id="wiz_single" />
                    <label for="wiz_single" class="ml-2 text-sm font-medium text-base-content/80 cursor-pointer">{{ $t('tenant.sources.wizard.singlePageLabel') }}</label>
                  </div>
                  <div v-if="!singlePageOnly" class="animate-fade-in pt-1">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2">{{ $t('tenant.sources.wizard.excludeLabel') }}</label>
                    <textarea v-model="excludedUrls" :placeholder="$t('tenant.sources.wizard.excludePlaceholder')" rows="2"
                      class="w-full p-3 bg-base-100 border border-base-200 rounded-xl text-sm focus:outline-none focus:border-primary/50 transition-colors"></textarea>
                  </div>
                </div>
              </div>

              <!-- Document form -->
              <div v-if="type === 'document'" class="space-y-5">
                <div class="relative border-2 border-dashed border-base-300 hover:border-primary/50 transition-colors p-8 rounded-2xl flex flex-col items-center justify-center bg-base-50 group">
                  <input id="wiz-file-upload" type="file" @change="handleFileSelect" accept=".pdf,.txt,.csv"
                    class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                  <div class="w-12 h-12 rounded-full bg-base-200 group-hover:bg-primary/10 group-hover:text-primary transition-colors flex items-center justify-center text-base-content/40 text-xl mb-3">
                    <font-awesome-icon :icon="['fas', 'file-arrow-up']" />
                  </div>
                  <p class="text-sm font-medium text-base-content/80 text-center" v-if="!selectedFile">PDF, TXT, CSV accepted</p>
                  <p class="text-sm font-bold text-primary text-center" v-else>{{ selectedFile.name }}</p>
                </div>
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
import { ref, computed } from 'vue';
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
const url = ref('');
const crawlMode = ref('soup');
const singlePageOnly = ref(false);
const excludedUrls = ref('');
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

const reset = () => {
  step.value = 0; type.value = null; url.value = ''; crawlMode.value = 'soup';
  singlePageOnly.value = false; excludedUrls.value = ''; selectedFile.value = null;
};

const submit = async () => {
  submitting.value = true;
  const tenantId = tenantsStore.currentTenant?.id;
  try {
    if (type.value === 'website') {
      await apiClient.post(`/tenants/${tenantId}/sources/discover`, {
        url: finalUrl.value,
        single_page_only: singlePageOnly.value,
        excluded_urls: singlePageOnly.value ? [] : excludedUrls.value.split('\n').filter(u => u.trim()),
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
</style>
