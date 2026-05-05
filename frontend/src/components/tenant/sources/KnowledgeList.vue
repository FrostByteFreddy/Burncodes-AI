<template>
  <div class="xl:col-span-7 bg-base-100 p-6 flex flex-col h-full xl:border-r border-base-200/50">
    <div class="mb-8">
      <h2 class="text-3xl font-display font-bold text-base-content tracking-tight mb-2">Active Sources</h2>
      <p class="text-base-content/60 text-sm">Manage the knowledge base context that trains your AI.</p>
    </div>

    <!-- Metrics -->
    <div class="grid grid-cols-2 gap-4 mb-10 shrink-0">
      <div class="bg-primary/5 rounded-2xl p-5 border border-primary/10">
        <p class="text-xs font-bold uppercase tracking-widest text-primary/70 mb-1">Total Documents</p>
        <p class="text-4xl font-black text-primary font-display leading-none">{{ fileSources.length }}</p>
      </div>
      <div class="bg-secondary/5 rounded-2xl p-5 border border-secondary/10">
        <p class="text-xs font-bold uppercase tracking-widest text-secondary/70 mb-1">Indexed Links</p>
        <p class="text-4xl font-black text-secondary font-display leading-none">{{ urlSources.length }}</p>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-10 pb-10">
      <div v-if="tenantsStore.loading" class="space-y-4">
        <div v-for="n in 3" :key="n" class="h-16 bg-base-200/50 rounded-xl animate-pulse"></div>
      </div>

      <div v-else>
        <!-- Live Jobs -->
        <div v-if="crawlingJobs.length > 0" class="mb-10 animate-fade-in">
          <h4 class="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-4 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span> Live Activity
          </h4>
          <div class="space-y-3">
            <div v-for="job in crawlingJobs" :key="job.id"
              class="bg-base-100 border border-base-200 p-4 rounded-2xl shadow-sm relative overflow-hidden">
              <div class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b"
                :class="{
                  'from-success/80 to-success/40': job.status === 'COMPLETED',
                  'from-primary/80 to-primary/40': job.status === 'IN_PROGRESS',
                  'from-error/80 to-error/40': job.status === 'FAILED',
                  'from-base-300 to-base-200': !['COMPLETED','IN_PROGRESS','FAILED'].includes(job.status)
                }"></div>
              <div class="pl-4">
                <p class="font-semibold text-sm truncate text-base-content" :title="job.start_url">{{ job.start_url }}</p>
                <div class="flex justify-between items-center mt-2">
                  <span class="text-xs font-bold tracking-wider"
                    :class="{
                      'text-success': job.status === 'COMPLETED',
                      'text-primary': job.status === 'IN_PROGRESS',
                      'text-error': job.status === 'FAILED',
                      'text-base-content/50': !['COMPLETED','IN_PROGRESS','FAILED'].includes(job.status)
                    }">{{ job.status }}</span>
                  <p class="text-xs text-base-content/40 font-medium">{{ new Date(job.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) }}</p>
                </div>
                <div class="mt-3" v-if="job.status === 'IN_PROGRESS'">
                  <CrawlingJobProgress :job="job" :tenantId="tenantsStore.currentTenant.id"
                    @job-completed="$emit('job-completed', job.id)"
                    @job-cancelled="$emit('job-cancelled', job.id)" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Documents -->
        <div class="mb-10">
          <h4 class="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-4">{{ $t("tenant.sources.existing.uploadedFiles") }}</h4>
          <div v-if="fileSources.length === 0" class="text-base-content/40 text-sm italic bg-base-200/20 p-4 rounded-xl border border-base-200 border-dashed text-center">No documents uploaded yet.</div>
          <div class="space-y-2">
            <div v-for="source in fileSources" :key="source.id"
              class="group bg-base-100 hover:bg-base-200/50 border border-base-200 p-4 rounded-2xl flex justify-between items-center transition-all duration-300">
              <div class="min-w-0 pr-4">
                <p class="font-semibold text-sm truncate text-base-content flex items-center gap-3">
                  <font-awesome-icon :icon="['fas', 'file-pdf']" class="text-primary/60" />{{ source.source_location }}
                </p>
                <p class="text-xs text-base-content/50 mt-1.5 flex items-center gap-2">
                  <span class="w-1.5 h-1.5 rounded-full" :class="source.status === 'COMPLETED' ? 'bg-success' : (source.status === 'ERROR' ? 'bg-error' : 'bg-primary')"></span>{{ source.status }}
                </p>
              </div>
              <button @click="$emit('delete', source)" class="btn btn-ghost btn-sm btn-circle text-base-content/30 hover:text-error hover:bg-error/10 opacity-0 group-hover:opacity-100 transition-opacity">
                <font-awesome-icon :icon="['fas', 'times']" />
              </button>
            </div>
          </div>
        </div>

        <!-- URLs -->
        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-base-content/50 mb-4">{{ $t("tenant.sources.existing.crawledUrls") }}</h4>
          <div v-if="urlSources.length === 0" class="text-base-content/40 text-sm italic bg-base-200/20 p-4 rounded-xl border border-base-200 border-dashed text-center">No URLs indexed yet.</div>
          <div class="space-y-2">
            <div v-for="source in urlSources" :key="source.id"
              class="group bg-base-100 hover:bg-base-200/50 border border-base-200 p-4 rounded-2xl flex justify-between items-center transition-all duration-300">
              <div class="min-w-0 pr-4">
                <p class="font-semibold text-sm truncate text-base-content flex items-center gap-3">
                  <font-awesome-icon :icon="['fas', 'globe']" class="text-secondary/60" />{{ source.source_location }}
                </p>
                <p class="text-xs text-base-content/50 mt-1.5 flex items-center gap-2">
                  <span class="w-1.5 h-1.5 rounded-full" :class="source.status === 'COMPLETED' ? 'bg-success' : (source.status === 'ERROR' ? 'bg-error' : 'bg-primary')"></span>{{ source.status }}
                </p>
              </div>
              <button @click="$emit('delete', source)" class="btn btn-ghost btn-sm btn-circle text-base-content/30 hover:text-error hover:bg-error/10 opacity-0 group-hover:opacity-100 transition-opacity">
                <font-awesome-icon :icon="['fas', 'times']" />
              </button>
            </div>
          </div>
        </div>

        <!-- Failed -->
        <div v-if="failedSources.length > 0" class="mt-10">
          <h4 class="text-xs font-bold uppercase tracking-wider text-error/70 mb-4 flex items-center gap-2">
            <font-awesome-icon :icon="['fas', 'circle-exclamation']" /> Failed Crawls &amp; Errors
          </h4>
          <div class="space-y-2">
            <div v-for="source in failedSources" :key="source.id"
              class="group bg-error/5 hover:bg-error/10 border border-error/20 p-4 rounded-2xl flex justify-between items-center transition-all duration-300">
              <div class="min-w-0 pr-4">
                <p class="font-semibold text-sm truncate text-base-content flex items-center gap-3">
                  <font-awesome-icon :icon="['fas', 'link-slash']" class="text-error/60" v-if="source.source_type === 'URL'" />
                  <font-awesome-icon :icon="['fas', 'file-circle-xmark']" class="text-error/60" v-else />
                  <span class="line-through opacity-70">{{ source.source_location }}</span>
                </p>
                <p class="text-xs text-error/80 mt-1.5 flex items-center gap-2 font-medium">
                  <span class="w-1.5 h-1.5 rounded-full bg-error"></span>
                  ERROR {{ source.status_code ? `(${source.status_code})` : '' }}
                </p>
              </div>
              <button @click="$emit('delete', source)" class="btn btn-ghost btn-sm btn-circle text-error/50 hover:text-error hover:bg-error/20 opacity-0 group-hover:opacity-100 transition-opacity">
                <font-awesome-icon :icon="['fas', 'times']" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useTenantsStore } from '../../../stores/tenants';
import CrawlingJobProgress from '../CrawlingJobProgress.vue';

const props = defineProps({ crawlingJobs: { type: Array, default: () => [] } });
defineEmits(['delete', 'job-completed', 'job-cancelled']);

const tenantsStore = useTenantsStore();

const urlSources = computed(() =>
  (tenantsStore.currentTenant?.tenant_sources || []).filter(s => s.source_type === 'URL' && s.status !== 'ERROR')
);
const fileSources = computed(() =>
  (tenantsStore.currentTenant?.tenant_sources || []).filter(s => s.source_type === 'FILE' && s.status !== 'ERROR')
);
const failedSources = computed(() =>
  (tenantsStore.currentTenant?.tenant_sources || []).filter(s => s.status === 'ERROR')
);
</script>
