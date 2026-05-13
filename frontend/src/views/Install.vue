<template>
  <div class="install-page">

    <!-- Left: description + chatbot link -->
    <div class="settings-section">
      <h3 class="settings-section__title">
        <font-awesome-icon :icon="['fas', 'rocket']" class="settings-section__icon" />
        {{ $t('tenant.install.title') }}
      </h3>
      <p class="step-subtext mb-4">{{ $t('tenant.install.description') }}</p>

      <div class="install-steps">
        <div class="install-step">
          <span class="install-step__num">1</span>
          <span>{{ $t('tenant.install.step1') }}</span>
        </div>
        <div class="install-step">
          <span class="install-step__num">2</span>
          <span>{{ $t('tenant.install.step2') }}</span>
        </div>
        <div class="install-step">
          <span class="install-step__num">3</span>
          <span>{{ $t('tenant.install.step3') }}</span>
        </div>
      </div>

      <a
        :href="`/preview.html?tenant_id=${tenantId}`"
        target="_blank"
        rel="noopener"
        class="starter-add-btn"
      >
        <font-awesome-icon :icon="['fas', 'comments']" />
        {{ $t('tenant.install.previewLink') }}
      </a>
    </div>

    <!-- Right: embed script -->
    <div class="settings-section">
      <h3 class="settings-section__title">
        <font-awesome-icon :icon="['fas', 'code']" class="settings-section__icon" />
        {{ $t('tenant.install.scriptTitle') }}
      </h3>
      <p class="step-subtext mb-4">{{ $t('tenant.install.scriptDesc') }}</p>

      <div class="install-script-block">
        <pre class="install-script-pre"><code>&lt;script
  src="{{ apiUrl }}/tenants/widget.js"
  data-tenant-id="{{ tenantId }}"&gt;
&lt;/script&gt;</code></pre>
        <button @click="copyScript" class="install-script-copy">
          <font-awesome-icon :icon="['fas', copied ? 'check' : 'copy']" />
          <span>{{ copied ? $t('tenant.install.copied') : $t('tenant.install.copy') }}</span>
        </button>
      </div>

      <p class="step-subtext mt-3">{{ $t('tenant.install.scriptHint') }}</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../stores/tenants';
import { useToast } from '../composables/useToast';

const tenantsStore = useTenantsStore();
const { t } = useI18n();
const { addToast } = useToast();

const tenantId = computed(() => tenantsStore.currentTenant?.id ?? '');
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
const copied = ref(false);

const copyScript = () => {
  const script = `<script src="${apiUrl}/tenants/widget.js" data-tenant-id="${tenantId.value}"><\/script>`;
  navigator.clipboard.writeText(script).then(() => {
    copied.value = true;
    addToast(t('tenant.settings.actions.scriptCopied'), 'success');
    setTimeout(() => { copied.value = false; }, 2000);
  }).catch(() => addToast(t('tenant.settings.actions.copyFailed'), 'error'));
};
</script>

<style scoped>
.install-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 860px) {
  .install-page { grid-template-columns: 1fr; }
}

/* ── Steps ─────────────────────────────────────────── */
.install-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.install-step {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
  color: var(--surface-text);
}

.install-step__num {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--surface-muted);
}

/* ── Preview link ── uses starter-add-btn from AppearanceTab.css */
</style>
