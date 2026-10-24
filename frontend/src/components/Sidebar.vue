<template>
  <!-- Desktop sidebar -->
  <aside class="sidebar" :class="{ 'sidebar--mobile-open': mobileOpen }">
    <!-- Logo -->
    <router-link to="/manage-tenants" class="sidebar__logo">
      <img src="/logo.png" alt="Logo" class="sidebar__logo-img" />
    </router-link>

    <!-- Tenant switcher -->
    <div class="sidebar__tenant" ref="tenantRef">
      <button class="tenant-pill" @click="tenantOpen = !tenantOpen">
        <span class="tenant-pill__dot"></span>
        <span class="tenant-pill__name">{{ activeTenant?.name ?? $t('sidebar.selectTenant') }}</span>
        <font-awesome-icon :icon="['fas', 'chevron-down']" class="tenant-pill__arrow" :class="{ 'rotate-180': tenantOpen }" />
      </button>
      <transition name="dropdown">
        <div v-if="tenantOpen" class="sidebar__dropdown">
          <a
            v-for="t in tenantsStore.tenants" :key="t.id"
            class="dropdown-row"
            :class="{ 'dropdown-row--active': t.id === activeTenant?.id }"
            href="#"
            @click.prevent="selectTenant(t)"
          >
            <span class="dropdown-row__dot" :class="{ 'dropdown-row__dot--active': t.id === activeTenant?.id }"></span>
            {{ t.name }}
          </a>
          <div class="dropdown-divider"></div>
          <button class="dropdown-row dropdown-row--new" @click="$emit('newTenant')">
            <font-awesome-icon :icon="['fas', 'plus']" />
            {{ $t('manageTenants.newTenant') }}
          </button>
        </div>
      </transition>
    </div>

    <!-- Workspace nav -->
    <div class="sidebar__section-label">{{ $t('sidebar.workspace') }}</div>
    <nav class="sidebar__nav" v-if="activeTenant">
      <router-link
        :to="{ name: 'TenantOverview', params: { tenantId: activeTenant.id } }"
        class="nav-item" active-class="nav-item--active"
      >
        <font-awesome-icon :icon="['fas', 'gauge']" class="nav-item__icon" />
        <span>{{ $t('sidebar.overview') }}</span>
      </router-link>
      <router-link
        :to="{ name: 'TenantSources', params: { tenantId: activeTenant.id } }"
        class="nav-item" active-class="nav-item--active"
      >
        <font-awesome-icon :icon="['fas', 'database']" class="nav-item__icon" />
        <span>{{ $t('sidebar.sources') }}</span>
      </router-link>
      <router-link
        :to="{ name: 'TenantConfigure', params: { tenantId: activeTenant.id } }"
        class="nav-item" active-class="nav-item--active"
      >
        <font-awesome-icon :icon="['fas', 'sliders']" class="nav-item__icon" />
        <span>{{ $t('sidebar.configure') }}</span>
      </router-link>
      <router-link
        :to="{ name: 'TenantInsights', params: { tenantId: activeTenant.id } }"
        class="nav-item" active-class="nav-item--active"
      >
        <font-awesome-icon :icon="['fas', 'chart-line']" class="nav-item__icon" />
        <span>{{ $t('sidebar.insights') }}</span>
      </router-link>
      <router-link
        :to="{ name: 'TenantInstall', params: { tenantId: activeTenant.id } }"
        class="nav-item" active-class="nav-item--active"
      >
        <font-awesome-icon :icon="['fas', 'code']" class="nav-item__icon" />
        <span>{{ $t('sidebar.install') }}</span>
      </router-link>
      <!-- Public, shareable chat page: a permalink anyone can open to try the chatbot -->
      <router-link
        :to="{ name: 'TenantTestPage', params: { tenantId: activeTenant.id } }"
        class="nav-item" active-class="nav-item--active"
      >
        <font-awesome-icon :icon="['fas', 'comments']" class="nav-item__icon" />
        <span>{{ $t('sidebar.chatbot') }}</span>
        <font-awesome-icon v-if="activeTenant.test_protected" :icon="['fas', 'lock']" class="nav-item__ext" :title="$t('testPage.link.protected')" />
      </router-link>
    </nav>

    <div class="sidebar__section-label">{{ $t('sidebar.account') }}</div>
    <nav class="sidebar__nav">
      <router-link to="/manage-tenants" class="nav-item" active-class="nav-item--active">
        <font-awesome-icon :icon="['fas', 'table-cells-large']" class="nav-item__icon" />
        <span>{{ $t('sidebar.manageTenants') }}</span>
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="sidebar__footer">
      <div class="sidebar__user">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-info">
          <p class="user-info__name">{{ userName }}</p>
          <p class="user-info__email">{{ authStore.user?.email }}</p>
        </div>
      </div>
      <div class="sidebar__footer-links">
        <router-link :to="{ name: 'AccountSettings', params: { section: 'profile' } }" class="footer-link" :class="{ 'footer-link--on': route.name === 'AccountSettings' }">
          <font-awesome-icon :icon="['fas', 'gear']" />
          {{ $t('sidebar.settings') }}
        </router-link>
        <button @click="handleLogout" class="footer-link footer-link--danger">
          <font-awesome-icon :icon="['fas', 'arrow-right-from-bracket']" />
          {{ $t('sidebar.logout') }}
        </button>
      </div>
    </div>
  </aside>

  <!-- Mobile overlay -->
  <div v-if="mobileOpen" class="sidebar-overlay" @click="$emit('closeMobile')"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useAuthStore } from '../stores/auth'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps({ mobileOpen: Boolean })
const emit = defineEmits(['newTenant', 'closeMobile'])

const tenantsStore = useTenantsStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const tenantOpen = ref(false)
const tenantRef = ref(null)

const activeTenant = computed(() => tenantsStore.currentTenant)


const userInitial = computed(() => {
  const meta = authStore.user?.user_metadata
  if (meta?.first_name) return meta.first_name[0].toUpperCase()
  return authStore.user?.email?.[0]?.toUpperCase() || '?'
})

const userName = computed(() => {
  const meta = authStore.user?.user_metadata
  if (meta?.first_name) return `${meta.first_name} ${meta.last_name || ''}`.trim()
  return authStore.user?.email?.split('@')[0] || ''
})

const selectTenant = (t) => {
  tenantOpen.value = false
  tenantsStore.selectTenant(t)
  router.push({ name: 'TenantSources', params: { tenantId: t.id } })
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

const handleOutsideClick = (e) => {
  if (tenantRef.value && !tenantRef.value.contains(e.target)) {
    tenantOpen.value = false
  }
}

onMounted(() => {
  tenantsStore.fetchTenants()
  document.addEventListener('click', handleOutsideClick)
})
onUnmounted(() => document.removeEventListener('click', handleOutsideClick))

watch(
  () => [tenantsStore.tenants, route.params.tenantId],
  ([tenants, tenantId]) => {
    if (tenantId) {
      const t = tenants.find(t => t.id === tenantId)
      if (t) tenantsStore.selectTenant(t)
    } else if (tenants.length === 1) {
      tenantsStore.selectTenant(tenants[0])
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
/* ── Sidebar Shell ─────────────────────────────────── */
/* Sticks beside the content inside the centered shell (see App.vue) */
.sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--surface-0);
  border-right: 1px solid var(--surface-3);
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  gap: 4px;
  z-index: 100;
  overflow-y: auto;
  overflow-x: hidden;
}

/* ── Logo ──────────────────────────────────────────── */
.sidebar__logo {
  display: block;
  padding: 4px 8px 16px;
  text-decoration: none;
}
.sidebar__logo-img {
  width: 90px;
  height: auto;
  max-width: 80px;
  display: block;
}

/* ── Tenant pill ───────────────────────────────────── */
.sidebar__tenant { position: relative; margin-bottom: 8px; }

.tenant-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-heading);
  font-size: var(--text-sm);
  font-weight: 700;
  cursor: pointer;
  transition: border-color var(--t-fast), background var(--t-fast);
  text-align: left;
}
.tenant-pill:hover { border-color: var(--interactive); }

.tenant-pill__dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--status-success);
  flex-shrink: 0;
}
.tenant-pill__name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tenant-pill__arrow {
  font-size: 10px;
  opacity: 0.5;
  transition: transform var(--t-fast);
}
.rotate-180 { transform: rotate(180deg); }

/* ── Dropdown ──────────────────────────────────────── */
.sidebar__dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  overflow: hidden;
  z-index: 200;
  box-shadow: var(--shadow-float);
}
.dropdown-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  font-size: var(--text-sm);
  color: var(--surface-text);
  cursor: pointer;
  transition: background var(--t-fast);
  text-decoration: none;
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
}
.dropdown-row:hover { background: var(--surface-2); }
.dropdown-row--active { color: var(--surface-heading); font-weight: 700; }
.dropdown-row--new { color: var(--interactive); }
.dropdown-row--new:hover { color: var(--surface-text); }
.dropdown-row__dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--surface-3);
  flex-shrink: 0;
}
.dropdown-row__dot--active { background: var(--interactive); }
.dropdown-divider { height: 1px; background: var(--surface-3); margin: 2px 0; }

/* Dropdown transition */
.dropdown-enter-active, .dropdown-leave-active { transition: opacity 0.15s, transform 0.15s; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Section labels ────────────────────────────────── */
/* Groups: things about the selected chatbot vs. the account */
.sidebar__section-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--surface-muted);
  padding: 18px 10px 6px;
}

/* ── Nav items ─────────────────────────────────────── */
.sidebar__nav { display: flex; flex-direction: column; gap: 1px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 500;
  color: var(--surface-muted);
  text-decoration: none;
  transition: color var(--t-fast), background var(--t-fast);
  position: relative;
}
.nav-item:hover { color: var(--surface-text); background: var(--surface-1); }
.nav-item--active {
  color: var(--surface-heading);
  background: var(--surface-1);
  font-weight: 700;
}
.nav-item--active::before {
  content: '';
  position: absolute;
  left: -12px; top: 8px; bottom: 8px;
  width: 3px;
  background: var(--interactive);
  border-radius: 0 3px 3px 0;
}
.nav-item__icon { width: 16px; color: inherit; flex-shrink: 0; }
.nav-item--active .nav-item__icon { color: var(--interactive); }
.nav-item--external { color: var(--surface-muted); }
.nav-item__ext { font-size: 10px; opacity: 0.4; margin-left: auto; }


/* ── Footer ────────────────────────────────────────── */
.sidebar__footer { margin-top: auto; padding-top: 12px; border-top: 1px solid var(--surface-3); }

.sidebar__user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  margin-bottom: 4px;
}
.user-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  color: var(--surface-heading);
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-info { overflow: hidden; }
.user-info__name { font-size: var(--text-sm); font-weight: 700; color: var(--surface-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-info__email { font-size: var(--text-xs); color: var(--surface-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar__footer-links { display: flex; flex-direction: column; gap: 1px; }

.footer-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--surface-muted);
  text-decoration: none;
  cursor: pointer;
  transition: color var(--t-fast), background var(--t-fast);
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
}
.footer-link:hover { color: var(--surface-text); background: var(--surface-1); }
.footer-link--on { color: var(--surface-heading); font-weight: 700; }
.footer-link--danger:hover { color: var(--status-error); background: var(--status-error-soft); }

/* ── Mobile overlay ────────────────────────────────── */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 99;
  backdrop-filter: blur(2px);
}

/* ── Mobile: sidebar off-canvas ────────────────────── */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0; top: 0; bottom: 0;
    height: auto;
    transform: translateX(-100%);
    transition: transform var(--t-normal);
    box-shadow: 8px 0 32px rgba(0,0,0,0.5);
  }
  .sidebar--mobile-open {
    transform: translateX(0);
    top: 56px;
  }
}
</style>
