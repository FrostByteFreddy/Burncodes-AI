<template>
  <div class="ins-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">{{ $t('pages.installTitle') }}</h1>
        <p class="page-lede">{{ $t('pages.install') }}</p>
      </div>
      <div class="page-actions">
        <Button as-child variant="outline"><a :href="`${baseUrl}preview.html?tenant_id=${tenantId}`" target="_blank" rel="noopener" class="inst-link">
          <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" /> {{ $t('install.example') }}
        </a></Button>
      </div>
    </div>

    <!-- Anything that would keep the chat button from showing up -->
    <p v-if="tenant && tenant.is_active === false" class="inst-note inst-note--warn">
      <font-awesome-icon :icon="['fas', 'power-off']" />
      <span>{{ $t('install.notes.off') }} <router-link :to="{ name: 'TenantOverview', params: { tenantId } }">{{ $t('install.notes.offLink') }}</router-link></span>
    </p>
    <p v-else-if="tenant?.widget_config?.widget_enabled === false" class="inst-note inst-note--warn">
      <font-awesome-icon :icon="['fas', 'eye-slash']" />
      <span>{{ $t('install.notes.hidden') }} <router-link :to="{ name: 'TenantConfigure', params: { tenantId } }">{{ $t('install.notes.hiddenLink') }}</router-link></span>
    </p>
    <p v-if="tenant?.test_protected" class="inst-note">
      <font-awesome-icon :icon="['fas', 'lock']" />
      <span>{{ $t('install.notes.protected') }} <router-link :to="{ name: 'TenantTestPage', params: { tenantId } }">{{ $t('install.notes.protectedLink') }}</router-link></span>
    </p>

    <!-- The three steps -->
    <BcPanel as="section"  >
      <ol class="inst-steps">
        <li class="inst-step">
          <span class="inst-step__num">1</span>
          <div class="inst-step__body">
            <h2 class="inst-step__title">{{ $t('install.step1.title') }}</h2>
            <p class="inst-step__text">{{ $t('install.step1.text') }}</p>
            <div class="inst-code">
              <pre><code>{{ snippet }}</code></pre>
              <BcButton variant="primary" type="button" class="inst-code__copy" @click="copy(snippet)">
                <font-awesome-icon :icon="['fas', copied ? 'check' : 'copy']" /> {{ copied ? $t('install.copied') : $t('install.copy') }}
              </BcButton>
            </div>
          </div>
        </li>

        <li class="inst-step">
          <span class="inst-step__num">2</span>
          <div class="inst-step__body">
            <h2 class="inst-step__title">{{ $t('install.step2.title') }}</h2>
            <p class="inst-step__text">{{ $t('install.step2.text') }}</p>

            <div class="inst-builders">
              <details v-for="b in BUILDERS" :key="b" class="inst-builder">
                <summary>
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="inst-builder__chevron" />
                  {{ $t(`install.builders.${b}.name`) }}
                </summary>
                <p>{{ $t(`install.builders.${b}.how`) }}</p>
              </details>
            </div>

            <div class="inst-delegate">
              <p>{{ $t('install.delegate.text') }}</p>
              <Button as-child variant="outline"><a :href="mailto" class="inst-link">
                <font-awesome-icon :icon="['fas', 'envelope']" /> {{ $t('install.delegate.button') }}
              </a></Button>
            </div>
          </div>
        </li>

        <li class="inst-step">
          <span class="inst-step__num">3</span>
          <div class="inst-step__body">
            <h2 class="inst-step__title">{{ $t('install.step3.title') }}</h2>
            <p class="inst-step__text">{{ $t('install.step3.text') }}</p>
            <ul class="inst-checks">
              <li>{{ $t('install.step3.cache') }}</li>
              <li>{{ $t('install.step3.consent') }}</li>
            </ul>
          </div>
        </li>
      </ol>
    </BcPanel>
  </div>
</template>

<script setup>
import { BcButton, BcPanel } from '@/components/ui';
import { Button } from '@/components/ui/button';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../stores/tenants';
import { useToast } from '../composables/useToast';

const tenantsStore = useTenantsStore();
const { t } = useI18n();
const { addToast } = useToast();

const baseUrl = import.meta.env.BASE_URL;
const BUILDERS = ['wordpress', 'wix', 'squarespace', 'webflow', 'other'];

const tenant = computed(() => tenantsStore.currentTenant);
const tenantId = computed(() => tenant.value?.id ?? '');
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
const snippet = computed(() => `<script src="${apiUrl}/tenants/widget.js" data-tenant-id="${tenantId.value}" defer><\/script>`);

const copied = ref(false);
const copy = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch { addToast(t('install.copyFailed'), 'error'); }
};

// A ready-to-send request for whoever maintains the website
const mailto = computed(() => {
  const subject = t('install.delegate.subject', { name: tenant.value?.name || '' });
  const body = t('install.delegate.body', { code: snippet.value });
  return `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});
</script>

<style scoped>
.ins-page { display: flex; flex-direction: column; gap: 20px; }
.inst-link { text-decoration: none; }

.inst-note { display: flex; gap: 8px; align-items: baseline; font-size: var(--text-sm); color: var(--surface-text); padding: 12px 16px; border-radius: var(--radius-lg); background: var(--surface-1); border: 1px solid var(--surface-3); }
.inst-note--warn { color: var(--status-warning); border-color: var(--status-warn); }
.inst-note a { color: inherit; font-weight: 600; }

/* Steps: a real sequence, so numbered */
.inst-steps { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.inst-step { display: grid; grid-template-columns: 36px minmax(0, 1fr); gap: 16px; padding: 24px 0; border-top: 1px solid var(--surface-3); }
.inst-step:first-child { border-top: none; padding-top: 0; }
.inst-step:last-child { padding-bottom: 0; }
.inst-step__num {
  width: 32px; height: 32px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--interactive-soft); color: var(--interactive); font-weight: 800;
}
.inst-step__body { min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.inst-step__title { font-size: var(--text-lg); font-weight: 700; color: var(--surface-heading); margin-top: 4px; }
.inst-step__text { font-size: 16px; color: var(--surface-text); max-width: var(--measure); line-height: var(--leading-body); }

.inst-code { margin-top: 8px; border-radius: var(--radius-lg); background: var(--surface-0); border: 1px solid var(--surface-3); overflow: hidden; }
.inst-code pre { margin: 0; padding: 16px; overflow-x: auto; font-size: 14px; line-height: 1.6; color: var(--surface-heading); }
.inst-code code { font-family: var(--font-mono); white-space: pre-wrap; word-break: break-all; }
.inst-code__copy { margin: 0 16px 16px; }

.inst-builders { margin-top: 8px; display: flex; flex-direction: column; border: 1px solid var(--surface-3); border-radius: var(--radius-lg); overflow: hidden; }
.inst-builder + .inst-builder { border-top: 1px solid var(--surface-3); }
.inst-builder summary { display: flex; align-items: center; gap: 8px; padding: 12px 16px; cursor: pointer; list-style: none; font-size: 16px; font-weight: 600; color: var(--surface-heading); }
.inst-builder summary::-webkit-details-marker { display: none; }
.inst-builder summary:hover { background: var(--surface-2); }
.inst-builder__chevron { font-size: 11px; color: var(--surface-muted); transition: transform var(--t-fast); }
.inst-builder[open] .inst-builder__chevron { transform: rotate(90deg); }
.inst-builder p { padding: 0 16px 16px 37px; font-size: var(--text-sm); color: var(--surface-text); line-height: var(--leading-body); max-width: var(--measure); }

.inst-delegate { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-top: 8px; padding: 16px 16px; border-radius: var(--radius-lg); background: var(--surface-2); }
.inst-delegate p { font-size: var(--text-sm); color: var(--surface-text); flex: 1; min-width: 220px; }

.inst-checks { margin: 4px 0 0; padding-left: 16px; display: flex; flex-direction: column; gap: 8px; font-size: var(--text-sm); color: var(--surface-muted); max-width: var(--measure); }

@media (prefers-reduced-motion: reduce) { .inst-builder__chevron { transition: none; } }
</style>
