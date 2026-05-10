<template>
  <div class="install-tab">

    <!-- Full-height chat preview -->
    <div class="install-tab__preview">
      <h3 class="install-section__title">
        <font-awesome-icon :icon="['fas', 'eye']" />
        Live Preview
      </h3>
      <iframe
        :src="`/chat/${tenantId}`"
        class="install-tab__iframe"
        title="Chat Preview"
      ></iframe>
    </div>

    <!-- Installation script -->
    <div class="install-tab__script">
      <h3 class="install-section__title">
        <font-awesome-icon :icon="['fas', 'code']" />
        {{ $t('tenant.settings.appearance.installation.title') }}
      </h3>
      <p class="install-section__sub">{{ $t('tenant.settings.appearance.installation.instruction') }}</p>
      <div class="install-script-block">
        <pre class="install-script-pre"><code>&lt;script src="{{ apiUrl }}/tenants/widget.js" data-tenant-id="{{ tenantId }}"&gt;&lt;/script&gt;</code></pre>
        <button @click.prevent="copyScript" class="install-script-copy">
          <font-awesome-icon :icon="['fas', 'copy']" />
          <span class="ml-1">{{ $t('tenant.settings.appearance.installation.copy') }}</span>
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n';
import { useToast } from '../../../composables/useToast';

const props = defineProps({
  tenantId: { type: String, required: true },
  apiUrl:   { type: String, default: '' },
});

const { t }        = useI18n();
const { addToast } = useToast();

const copyScript = () => {
  const script = `<script src="${props.apiUrl}/tenants/widget.js" data-tenant-id="${props.tenantId}"><\/script>`;
  navigator.clipboard.writeText(script)
    .then(() => addToast(t('tenant.settings.actions.scriptCopied'), 'success'))
    .catch(() => addToast(t('tenant.settings.actions.copyFailed'), 'error'));
};
</script>

<style scoped>
.install-tab {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.install-section__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--surface-heading);
  margin-bottom: 12px;
}
.install-section__sub {
  font-size: 13px;
  color: var(--surface-muted);
  margin-bottom: 16px;
  line-height: 1.5;
}

/* ── Preview iframe ────────────────────────────────── */
.install-tab__iframe {
  width: 100%;
  height: 75svh;
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  background: var(--surface-2);
}
</style>
