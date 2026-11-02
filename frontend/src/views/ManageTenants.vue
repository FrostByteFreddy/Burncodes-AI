<template>
  <div class="mt-page">
    <BcPageHeader :title="$t('manageTenants.title')" :lede="$t('pages.chatbots')">
      <template v-if="tenantsStore.tenants.length" #actions>
        <BcButton variant="primary" icon="plus" @click="showCreateModal = true">{{ $t('manageTenants.newChatbot') }}</BcButton>
      </template>
    </BcPageHeader>

    <BcPanel v-if="tenantsStore.loading && !tenantsStore.tenants.length" flush>
      <div v-for="n in 3" :key="n" class="mt-row"><BcSkeleton :lines="2" /></div>
    </BcPanel>

    <BcEmptyState v-else-if="!tenantsStore.tenants.length" icon="layer-group" :title="$t('manageTenants.noChatbots')" :description="$t('manageTenants.noChatbotsSubtitle')">
      <template #action>
        <Button as-child variant="default" size="lg"><router-link :to="{ path: '/onboarding', query: { onboarding: '' } }" >{{ $t('manageTenants.guided') }}</router-link></Button>
        <BcButton variant="quiet" @click="showCreateModal = true">{{ $t('manageTenants.createChatbot') }}</BcButton>
      </template>
    </BcEmptyState>

    <BcPanel v-else flush>
      <ul class="mt-list">
        <li v-for="tenant in tenantsStore.tenants" :key="tenant.id" class="mt-row">
          <router-link :to="{ name: 'TenantOverview', params: { tenantId: tenant.id } }" class="mt-main" @click="tenantsStore.selectTenant(tenant)">
            <span class="mt-name">{{ tenant.name }}</span>
            <span class="mt-meta">
              {{ $t('manageTenants.sources', { n: formatNumber(sourceCount(tenant)) }, sourceCount(tenant)) }}
             , {{ $t(`configure.basics.audiences.${tenant.audience || 'municipality'}`) }}
            </span>
          </router-link>
          <BcStatusBadge :status="tenant.is_active === false ? 'off' : 'on'" size="sm" />
          <div class="mt-actions">
            <a :href="`/chat/${tenant.id}`" target="_blank" rel="noopener" class="bc-iconbtn bc-iconbtn--quiet bc-iconbtn--md"
              :aria-label="$t('manageTenants.openChatbot')" :title="$t('manageTenants.openChatbot')"><BcIcon name="arrow-up-right-from-square" /></a>
            <router-link :to="{ name: 'TenantConfigure', params: { tenantId: tenant.id } }" class="bc-iconbtn bc-iconbtn--quiet bc-iconbtn--md"
              :aria-label="$t('manageTenants.configure')" :title="$t('manageTenants.configure')"><BcIcon name="sliders" /></router-link>
            <BcIconButton icon="trash" variant="danger" :label="$t('manageTenants.delete')" @click="tenantToDelete = tenant" />
          </div>
        </li>
      </ul>
    </BcPanel>

    <CreateTenantModal v-if="showCreateModal" @close="showCreateModal = false" />
    <ConfirmationModal
      :show="Boolean(tenantToDelete)"
      :title="$t('manageTenants.deleteModal.title')"
      :message="$t('manageTenants.deleteModal.message', { name: escapeHtml(tenantToDelete?.name) })"
      :confirm-button-text="$t('manageTenants.deleteModal.confirm')"
      :loading="deleting"
      @confirm="deleteTenant"
      @cancel="tenantToDelete = null"
    />
  </div>
</template>

<script setup>
import { Button } from '@/components/ui/button';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../stores/tenants';
import { useToast } from '../composables/useToast';
import { formatNumber } from '../utils/format';
import CreateTenantModal from '../components/CreateTenantModal.vue';
import ConfirmationModal from '../components/ConfirmationModal.vue';
import {
  BcButton, BcEmptyState, BcIcon, BcIconButton, BcPageHeader, BcPanel, BcSkeleton, BcStatusBadge,
} from '../components/ui';

const { t } = useI18n();
const tenantsStore = useTenantsStore();
const { addToast } = useToast();

const showCreateModal = ref(false);
const tenantToDelete = ref(null);
const deleting = ref(false);

// the list endpoint returns the count as tenant_sources: [{ count }]
const sourceCount = (tenant) => tenant.source_count ?? tenant.tenant_sources?.[0]?.count ?? 0;
const escapeHtml = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const deleteTenant = async () => {
  deleting.value = true;
  try {
    await tenantsStore.deleteTenant(tenantToDelete.value.id);
    addToast(t('manageTenants.toast.deleteSuccess'), 'success');
  } catch (e) {
    addToast(t(e.response?.data?.code === 'gemini_failed' ? 'common.geminiFailed' : 'manageTenants.toast.deleteError'), 'error');
  } finally {
    deleting.value = false;
    tenantToDelete.value = null;
  }
};
</script>

<style scoped>
.mt-page { display: flex; flex-direction: column; gap: var(--space-8); }
.mt-list { list-style: none; margin: 0; padding: 0; }
.mt-row {
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-4) var(--space-5); border-top: 1px solid var(--border-subtle);
}
.mt-row:first-child { border-top: none; }
.mt-main { flex: 1; min-width: 0; display: flex; flex-direction: column; text-decoration: none; color: inherit; }
.mt-main:hover .mt-name { color: var(--interactive); }
.mt-name { font-size: 18px; line-height: 26px; font-weight: 700; color: var(--text-primary); }
.mt-meta { font-size: 14px; line-height: 20px; color: var(--text-secondary); }
.mt-actions { display: flex; gap: var(--space-1); }
</style>
