<template>
  <div class="ts">
    <BcPageHeader :title="$t('botSettings.title')" :lede="$t('botSettings.lede')" />

    <BcSkeleton v-if="!tenant" :lines="6" />
    <template v-else>
      <!-- Who it answers -->
      <BcSection :title="$t('configure.basics.audience')" :description="$t('configure.basics.audienceHint')">
        <BcRadioCards :model-value="tenant.audience || DEFAULT_AUDIENCE" :options="audienceOptions" :disabled="saving"
          @update:model-value="(v) => save({ audience: v })" />
      </BcSection>

      <!-- What it learns with -->
      <BcSection :title="$t('botSettings.model.title')" :description="$t('botSettings.model.sub')">
        <BcRadioCards :model-value="tenant.learning_model || 'argon'" :options="modelOptions" :columns="1"
          @update:model-value="(v) => save({ learning_model: v })" />
      </BcSection>

      <!-- What runs by itself -->
      <BcSection :title="$t('overview.auto.title')" :description="$t('overview.auto.sub')">
        <BcPanel>
          <div class="ts-auto">
            <div class="ts-auto__row">
              <div>
                <p class="ts-auto__name">{{ $t('settings.schedules.websites') }}</p>
                <p class="ts-muted">{{ $t('overview.auto.recrawlHow') }}</p>
              </div>
              <BcSelect :model-value="tenant.auto_recrawl ? String(tenant.recrawl_interval_days || 7) : 'off'" :options="recrawlOptions"
                :aria-label="$t('settings.schedules.websites')"
                @update:model-value="(v) => save(v === 'off' ? { auto_recrawl: false } : { auto_recrawl: true, recrawl_interval_days: Number(v) })" />
            </div>
            <div class="ts-auto__row">
              <div>
                <p class="ts-auto__name">{{ $t('settings.schedules.reviews') }}</p>
                <p class="ts-muted">{{ $t('settings.schedules.reviewNote') }}</p>
              </div>
              <BcSelect :model-value="tenant.review_chats ? String(tenant.review_interval_days || 1) : 'off'" :options="reviewOptions"
                :aria-label="$t('settings.schedules.reviews')"
                @update:model-value="(v) => save(v === 'off' ? { review_chats: false } : { review_chats: true, review_interval_days: Number(v) })" />
            </div>
          </div>
        </BcPanel>
      </BcSection>

      <!-- What every run leaves out -->
      <BcSection :title="$t('botSettings.excluded.title')" :description="$t('settings.schedules.excludedNote')">
        <BcPanel v-if="excluded.length" flush>
          <ul class="ts-list">
            <li v-for="r in excluded" :key="r.path || r.url" class="ts-list__row">
              <BcIcon :name="r.path ? 'folder' : 'file-lines'" class="ts-list__icon" />
              <span class="ts-list__label">
                {{ r.title || r.path || r.url }}
                <span v-if="r.title" class="ts-muted">{{ r.path || r.url }}</span>
              </span>
              <BcButton variant="quiet" size="sm" :disabled="saving" @click="removeExclusion(r)">{{ $t('settings.schedules.excludedRemove') }}</BcButton>
            </li>
          </ul>
        </BcPanel>
        <BcEmptyState v-else compact icon="folder" :title="$t('botSettings.excluded.none')" :description="$t('botSettings.excluded.how')" />
      </BcSection>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useTenantsStore } from '@/stores/tenants';
import { useToast } from '@/composables/useToast';
import { AUDIENCES, DEFAULT_AUDIENCE } from '@/utils/chatbotDefaults';
import { LEARNING_MODELS } from '@/composables/useLearningModels';
import {
  BcButton, BcEmptyState, BcIcon, BcPageHeader, BcPanel, BcRadioCards, BcSection, BcSelect, BcSkeleton,
} from '@/components/ui';

// Everything that belongs to one chatbot rather than to its look or the account
const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();
const tenant = computed(() => tenantsStore.currentTenant);
const saving = ref(false);

const audienceOptions = computed(() => AUDIENCES.map((key) => ({
  value: key, icon: key === 'municipality' ? 'landmark' : 'store',
  title: t(`configure.basics.audiences.${key}`), description: t(`configure.basics.audiences.${key}Desc`),
})));
const modelOptions = computed(() => LEARNING_MODELS.map((key) => ({
  value: key, title: t(`knowledge.models.${key}.title`), description: t(`knowledge.models.${key}.desc`),
})));
const recrawlOptions = computed(() => [
  { value: 'off', label: t('settings.schedules.off') },
  ...[7, 14, 30].map((n) => ({ value: String(n), label: t(`knowledge.recrawl.every${n}`) })),
]);
const reviewOptions = computed(() => [
  { value: 'off', label: t('settings.schedules.off') },
  { value: '1', label: t('overview.auto.daily') },
  { value: '7', label: t('overview.auto.weekly') },
]);

// Only "leave out" rules are listed; "keep" rules are exceptions inside them
const excluded = computed(() => (tenant.value?.crawl_exclusions || []).filter((r) => r.exclude));
const inside = (path, folder) => path === folder || path.startsWith(`${folder.replace(/\/$/, '')}/`);
const removeExclusion = (rule) => save({
  crawl_exclusions: (tenant.value.crawl_exclusions || []).filter((r) => r !== rule
    // a folder's exceptions go with it
    && !(rule.path && r.path && !r.exclude && inside(r.path, rule.path))),
});

// Each choice saves right away
async function save(payload) {
  saving.value = true;
  try {
    await apiClient.put(`/tenants/${tenant.value.id}`, payload);
    Object.assign(tenantsStore.currentTenant, payload);
    addToast(t('settings.saved'), 'success');
  } catch {
    addToast(t('tenant.settings.actions.saveFailed'), 'error');
    await tenantsStore.refetch(tenant.value.id);
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.ts { display: flex; flex-direction: column; }
.ts-muted { color: var(--text-secondary); font-size: 14px; line-height: 20px; }
.ts-auto { display: flex; flex-direction: column; }
.ts-auto__row { display: flex; align-items: center; justify-content: space-between; gap: var(--space-6); padding: var(--space-4) 0; }
.ts-auto__row + .ts-auto__row { border-top: 1px solid var(--border-subtle); }
.ts-auto__row:first-child { padding-top: 0; }
.ts-auto__row:last-child { padding-bottom: 0; }
.ts-auto__row :deep(.bc-select) { width: 220px; flex: none; }
.ts-auto__name { font-weight: 600; }
.ts-list { list-style: none; margin: 0; padding: 0; }
.ts-list__row { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-5); border-top: 1px solid var(--border-subtle); }
.ts-list__row:first-child { border-top: none; }
.ts-list__icon { color: var(--text-tertiary); }
.ts-list__label { flex: 1; min-width: 0; display: flex; flex-direction: column; }

@media (max-width: 700px) {
  .ts-auto__row { flex-direction: column; align-items: stretch; gap: var(--space-3); }
  .ts-auto__row :deep(.bc-select) { width: 100%; }
}
</style>
