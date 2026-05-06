<template>
  <div class="page">
    <div class="page-header">
      <p class="page-label">{{ $t('manageTenants.title').toUpperCase() }}</p>
      <button v-if="tenantsStore.tenants.length > 0" @click="showCreateModal = true" class="btn-add">
        <font-awesome-icon :icon="['fas', 'plus']" />
        {{ $t('manageTenants.newChatbot') }}
      </button>
    </div>

    <!-- Loading skeletons -->
    <div v-if="tenantsStore.loading && tenantsStore.tenants.length === 0" class="tenant-list">
      <div v-for="n in 3" :key="n" class="skeleton-card"></div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!tenantsStore.loading && tenantsStore.tenants.length === 0" class="empty-state">
      <p class="empty-state__title">{{ $t('manageTenants.noChatbots') }}</p>
      <p class="empty-state__sub">{{ $t('manageTenants.noChatbotsSubtitle') }}</p>
      <button @click="showCreateModal = true" class="btn-add">
        <font-awesome-icon :icon="['fas', 'plus']" />
        {{ $t('manageTenants.createChatbot') }}
      </button>
    </div>

    <!-- Tenant list -->
    <div v-else class="tenant-list">
      <div
        v-for="tenant in tenantsStore.tenants"
        :key="tenant.id"
        class="tenant-card"
        @click="goToTenant(tenant)"
      >
        <div class="tenant-card__left">
          <span class="status-dot" :class="tenant.sources?.length ? 'status-dot--active' : ''"></span>
          <div class="tenant-card__info">
            <h2 class="tenant-card__name">{{ tenant.name }}</h2>
            <p class="tenant-card__meta">
              <span>{{ $t('manageTenants.sources', { n: tenant.sources?.length ?? 0 }) }}</span>
              <span class="meta-sep">·</span>
              <span class="tenant-card__url">/chat/{{ tenant.id.slice(0, 8) }}…</span>
            </p>
          </div>
        </div>

        <div class="tenant-card__actions" @click.stop>
          <a
            :href="`/chat/${tenant.id}`"
            target="_blank"
            class="btn-ghost-sm"
            :title="$t('manageTenants.openChatbot')"
          >
            <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" />
          </a>
          <router-link
            :to="{ name: 'TenantConfigure', params: { tenantId: tenant.id } }"
            class="btn-ghost-sm"
            :title="$t('manageTenants.configure')"
          >
            <font-awesome-icon :icon="['fas', 'sliders']" />
          </router-link>
          <button
            @click="confirmDelete(tenant)"
            class="btn-ghost-sm btn-ghost-sm--danger"
            :title="$t('manageTenants.delete')"
          >
            <font-awesome-icon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>
    </div>

    <CreateTenantModal v-if="showCreateModal" @close="showCreateModal = false" />
    <ConfirmationModal
      v-if="tenantToDelete"
      :title="$t('manageTenants.deleteModal.title')"
      :message="$t('manageTenants.deleteModal.message', { name: tenantToDelete.name })"
      :confirmText="$t('manageTenants.deleteModal.confirm')"
      @confirm="deleteTenant"
      @cancel="tenantToDelete = null"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTenantsStore } from '../stores/tenants'
import { useToast } from '../composables/useToast'
import { useI18n } from 'vue-i18n'
import CreateTenantModal from '../components/CreateTenantModal.vue'
import ConfirmationModal from '../components/ConfirmationModal.vue'

const { t } = useI18n()
const tenantsStore = useTenantsStore()
const router = useRouter()
const { addToast } = useToast()

const showCreateModal = ref(false)
const tenantToDelete = ref(null)

const goToTenant = (tenant) => {
  tenantsStore.selectTenant(tenant)
  router.push({ name: 'TenantSources', params: { tenantId: tenant.id } })
}

const confirmDelete = (tenant) => { tenantToDelete.value = tenant }

const deleteTenant = async () => {
  try {
    await tenantsStore.deleteTenant(tenantToDelete.value.id)
    addToast(t('manageTenants.toast.deleteSuccess'), 'success')
  } catch {
    addToast(t('manageTenants.toast.deleteError'), 'error')
  } finally {
    tenantToDelete.value = null
  }
}
</script>

<style scoped>
.page { max-width: 720px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}

.page-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--surface-muted);
}

.btn-add {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--gradient-brand);
  color: white;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: opacity var(--t-fast), transform var(--t-fast);
}
.btn-add:hover { opacity: 0.9; transform: translateY(-1px); }

.btn-ghost-sm {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px; height: 32px;
  border-radius: var(--radius-md);
  background: none;
  border: none;
  color: var(--surface-muted);
  cursor: pointer;
  transition: color var(--t-fast), background var(--t-fast);
  text-decoration: none;
  font-size: 13px;
}
.btn-ghost-sm:hover { color: var(--surface-text); background: var(--surface-2); }
.btn-ghost-sm--danger:hover { color: var(--status-error); background: rgba(255,68,68,0.08); }

.tenant-list { display: flex; flex-direction: column; gap: 10px; }

.tenant-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: border-color var(--t-fast), box-shadow var(--t-fast), transform var(--t-fast);
}
.tenant-card:hover {
  border-color: rgba(10,31,171,0.4);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.tenant-card__left { display: flex; align-items: center; gap: 14px; }

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--surface-3);
  flex-shrink: 0;
}
.status-dot--active {
  background: var(--status-success);
  box-shadow: 0 0 6px var(--status-success);
}

.tenant-card__name {
  font-size: 15px;
  font-weight: 600;
  color: var(--surface-heading);
  margin-bottom: 3px;
}
.tenant-card__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--surface-muted);
}
.meta-sep { opacity: 0.4; }
.tenant-card__url { font-family: monospace; font-size: 11px; }

.tenant-card__actions { display: flex; align-items: center; gap: 4px; }

.skeleton-card {
  height: 70px;
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.empty-state {
  text-align: center;
  padding: 64px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.empty-state__title { font-size: 18px; font-weight: 600; color: var(--surface-heading); }
.empty-state__sub { font-size: 14px; color: var(--surface-muted); max-width: 380px; }
</style>
