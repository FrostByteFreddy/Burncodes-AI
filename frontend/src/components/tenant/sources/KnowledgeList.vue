<template>
  <div class="knowledge-panel">
    <div class="knowledge-header">
      <h2 class="knowledge-title">Active Sources</h2>
      <p class="knowledge-subtitle">Manage the knowledge base context that trains your AI.</p>
    </div>

    <div class="metric-grid">
      <div class="metric-card metric-card--primary">
        <p class="metric-label metric-label--primary">Total Documents</p>
        <p class="metric-value metric-value--primary">{{ fileSources.length }}</p>
      </div>
      <div class="metric-card metric-card--secondary">
        <p class="metric-label metric-label--secondary">Indexed Links</p>
        <p class="metric-value metric-value--secondary">{{ urlSources.length }}</p>
      </div>
    </div>

    <div class="source-scroll">
      <!-- Skeleton -->
      <div v-if="tenantsStore.loading" class="space-y-4">
        <div v-for="n in 3" :key="n" class="skeleton-row"></div>
      </div>

      <div v-else>
        <!-- Live Jobs -->
        <div v-if="crawlingJobs.length > 0" class="source-section animate-fade-in">
          <h4 class="source-section-title source-section-title--live">
            <span class="live-dot"></span> Live Activity
          </h4>
          <div class="space-y-3">
            <div v-for="job in crawlingJobs" :key="job.id" class="job-card">
              <div class="job-card__bar"
                :class="{
                  'job-card__bar--completed':  job.status === 'COMPLETED',
                  'job-card__bar--processing': job.status === 'IN_PROGRESS',
                  'job-card__bar--failed':     job.status === 'FAILED',
                  'job-card__bar--default':    !['COMPLETED','IN_PROGRESS','FAILED'].includes(job.status)
                }"></div>
              <div class="job-card__body">
                <p class="job-card__url" :title="job.start_url">{{ job.start_url }}</p>
                <div class="job-card__footer">
                  <span class="job-status"
                    :class="{
                      'job-status--completed':  job.status === 'COMPLETED',
                      'job-status--processing': job.status === 'IN_PROGRESS',
                      'job-status--failed':     job.status === 'FAILED',
                      'job-status--default':    !['COMPLETED','IN_PROGRESS','FAILED'].includes(job.status)
                    }">{{ job.status }}</span>
                  <p class="job-card__time">{{ new Date(job.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) }}</p>
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
        <div class="source-section">
          <h4 class="source-section-title">{{ $t("tenant.sources.existing.uploadedFiles") }}</h4>
          <div v-if="fileSources.length === 0" class="empty-state">No documents uploaded yet.</div>
          <div class="space-y-2">
            <div v-for="source in fileSources" :key="source.id" class="source-item">
              <div class="source-item__body">
                <p class="source-item__name">
                  <font-awesome-icon :icon="['fas', 'file-pdf']" class="text-primary/60" />
                  {{ source.source_location }}
                </p>
                <p class="source-item__meta">
                  <span class="status-dot"
                    :class="source.status === 'COMPLETED' ? 'status-dot--success' : source.status === 'ERROR' ? 'status-dot--error' : 'status-dot--processing'"></span>
                  {{ source.status }}
                </p>
              </div>
              <button @click="$emit('delete', source)" class="source-item__delete">
                <font-awesome-icon :icon="['fas', 'times']" />
              </button>
            </div>
          </div>
        </div>

        <!-- URLs -->
        <div class="source-section">
          <h4 class="source-section-title">{{ $t("tenant.sources.existing.crawledUrls") }}</h4>
          <div v-if="urlSources.length === 0" class="empty-state">No URLs indexed yet.</div>
          <div class="space-y-2">
            <div v-for="source in urlSources" :key="source.id" class="source-item">
              <div class="source-item__body">
                <p class="source-item__name">
                  <font-awesome-icon :icon="['fas', 'globe']" class="text-secondary/60" />
                  {{ source.source_location }}
                </p>
                <p class="source-item__meta">
                  <span class="status-dot"
                    :class="source.status === 'COMPLETED' ? 'status-dot--success' : source.status === 'ERROR' ? 'status-dot--error' : 'status-dot--processing'"></span>
                  {{ source.status }}
                </p>
              </div>
              <button @click="$emit('delete', source)" class="source-item__delete">
                <font-awesome-icon :icon="['fas', 'times']" />
              </button>
            </div>
          </div>
        </div>

        <!-- Failed -->
        <div v-if="failedSources.length > 0" class="source-section">
          <h4 class="source-section-title source-section-title--error">
            <font-awesome-icon :icon="['fas', 'circle-exclamation']" /> Failed Crawls &amp; Errors
          </h4>
          <div class="space-y-2">
            <div v-for="source in failedSources" :key="source.id" class="source-item source-item--error">
              <div class="source-item__body">
                <p class="source-item__name">
                  <font-awesome-icon :icon="['fas', 'link-slash']" class="text-error/60" v-if="source.source_type === 'URL'" />
                  <font-awesome-icon :icon="['fas', 'file-circle-xmark']" class="text-error/60" v-else />
                  <span class="source-item__name--struck">{{ source.source_location }}</span>
                </p>
                <p class="source-item__meta source-item__meta--error">
                  <span class="status-dot status-dot--error"></span>
                  ERROR {{ source.status_code ? `(${source.status_code})` : '' }}
                </p>
              </div>
              <button @click="$emit('delete', source)" class="source-item__delete source-item__delete--error">
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
