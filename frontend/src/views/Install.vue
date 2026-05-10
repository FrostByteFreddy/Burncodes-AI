<template>
  <div class="install-page">

    <!-- Left: description + chatbot link -->
    <div class="install-card install-card--info">
      <div class="install-card__icon-wrap">
        <font-awesome-icon :icon="['fas', 'rocket']" />
      </div>
      <h1 class="install-card__title">{{ $t('tenant.install.title') }}</h1>
      <p class="install-card__desc">{{ $t('tenant.install.description') }}</p>

      <div class="install-card__steps">
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
        :href="`/chat/${tenantId}`"
        target="_blank"
        rel="noopener"
        class="install-preview-btn"
      >
        <font-awesome-icon :icon="['fas', 'comments']" />
        {{ $t('tenant.install.previewLink') }}
        <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="install-preview-btn__ext" />
      </a>
    </div>

    <!-- Right: script -->
    <div class="install-card install-card--script">
      <div class="install-card__icon-wrap install-card__icon-wrap--accent">
        <font-awesome-icon :icon="['fas', 'code']" />
      </div>
      <h2 class="install-card__title">{{ $t('tenant.install.scriptTitle') }}</h2>
      <p class="install-card__desc">{{ $t('tenant.install.scriptDesc') }}</p>

      <div class="install-script-block">
        <pre class="install-script-pre"><code>&lt;script src="{{ apiUrl }}/tenants/widget.js" data-tenant-id="{{ tenantId }}"&gt;&lt;/script&gt;</code></pre>
        <button @click="copyScript" class="install-script-copy">
          <font-awesome-icon :icon="['fas', copied ? 'check' : 'copy']" />
          <span>{{ copied ? $t('tenant.install.copied') : $t('tenant.install.copy') }}</span>
        </button>
      </div>

      <p class="install-script-hint">{{ $t('tenant.install.scriptHint') }}</p>
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
  padding: 0;
  max-width: 900px;
}

@media (max-width: 768px) {
  .install-page { grid-template-columns: 1fr; }
}

/* ── Cards ─────────────────────────────────────────── */
.install-card {
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  padding: 32px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.install-card__icon-wrap {
  width: 44px; height: 44px;
  border-radius: var(--radius-md);
  background: rgba(10,31,171,0.12);
  color: var(--brand-indigo);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.install-card__icon-wrap--accent {
  background: rgba(0,224,255,0.1);
  color: var(--brand-cyan);
}

.install-card__title {
  font-size: 20px;
  font-weight: 800;
  color: var(--surface-heading);
  line-height: 1.2;
}

.install-card__desc {
  font-size: 13px;
  color: var(--surface-muted);
  line-height: 1.6;
}

/* ── Steps ─────────────────────────────────────────── */
.install-card__steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 4px 0;
}

.install-step {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--surface-text);
}

.install-step__num {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: white;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ── Preview link ──────────────────────────────────── */
.install-preview-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: var(--gradient-brand);
  color: white;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  margin-top: 8px;
  transition: opacity var(--t-fast), transform var(--t-fast);
  align-self: flex-start;
}
.install-preview-btn:hover { opacity: 0.9; transform: translateY(-1px); }
.install-preview-btn__ext { font-size: 10px; opacity: 0.7; }

/* ── Script block ──────────────────────────────────── */
.install-script-block {
  position: relative;
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.install-script-pre {
  margin: 0;
  padding: 16px;
  font-size: 12px;
  font-family: 'Fira Code', 'Fira Mono', monospace;
  color: var(--brand-cyan);
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
}

.install-script-copy {
  display: flex;
  align-items: center;
  gap: 7px;
  width: 100%;
  padding: 10px 16px;
  background: var(--surface-2);
  border: none;
  border-top: 1px solid var(--surface-3);
  color: var(--surface-text);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast);
}
.install-script-copy:hover { background: var(--surface-3); color: var(--surface-heading); }

.install-script-hint {
  font-size: 12px;
  color: var(--surface-muted);
  line-height: 1.5;
}
</style>
