<template>
  <!-- Desktop sidebar -->
  <aside class="sidebar" :class="{ 'sidebar--collapsed': mobileOpen === false }">
    <!-- Logo -->
    <router-link to="/manage-tenants" class="sidebar__logo">
      <svg width="90" height="36" viewBox="0 0 476 294" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M37.5312 140H1.69141C1.17057 140 0.910156 139.674 0.910156 139.023L1.30078 1.62109C1.30078 1.10026 1.5612 0.839844 2.08203 0.839844H40.5586C48.0456 0.839844 54.849 2.66276 60.9688 6.30859C66.9583 9.95443 71.6784 14.8047 75.1289 20.8594C78.5794 26.849 80.3047 33.3594 80.3047 40.3906C80.3047 46.1198 79.0026 51.4583 76.3984 56.4062C73.7943 61.3542 70.7018 65.3581 67.1211 68.418C70.9622 72.2591 73.957 76.7188 76.1055 81.7969C78.2539 86.875 79.3281 92.2135 79.3281 97.8125C79.3281 105.56 77.4727 112.624 73.7617 119.004C69.9857 125.384 64.9401 130.495 58.625 134.336C52.3099 138.112 45.2786 140 37.5312 140ZM40.5586 24.5703H25.3242V56.0156H40.5586C45.181 56.0156 48.9245 54.388 51.7891 51.1328C54.6536 47.8125 56.0859 44.2318 56.0859 40.3906C56.0859 36.1589 54.556 32.4805 51.4961 29.3555C48.4362 26.1654 44.7904 24.5703 40.5586 24.5703ZM37.5312 80.2344H25.3242L25.1289 115.586H37.5312C42.349 115.586 46.4831 113.828 49.9336 110.312C53.3841 106.797 55.1094 102.63 55.1094 97.8125C55.1094 92.9948 53.3841 88.8607 49.9336 85.4102C46.4831 81.9596 42.349 80.2344 37.5312 80.2344ZM130.5 141.953C123.469 141.953 116.958 140.13 110.969 136.484C104.979 132.839 100.194 127.956 96.6133 121.836C93.0977 115.651 91.3398 108.913 91.3398 101.621L91.7305 1.62109C91.7305 1.10026 91.9909 0.839844 92.5117 0.839844H114.973C115.493 0.839844 115.754 1.10026 115.754 1.62109V101.621C115.754 106.113 117.186 109.954 120.051 113.145C122.915 116.27 126.398 117.832 130.5 117.832C134.797 117.832 138.378 116.27 141.242 113.145C144.107 109.954 145.539 106.113 145.539 101.621V1.62109C145.539 1.10026 145.799 0.839844 146.32 0.839844H168.781C169.302 0.839844 169.562 1.10026 169.562 1.62109L169.953 101.621C169.953 108.978 168.195 115.749 164.68 121.934C161.099 128.053 156.346 132.936 150.422 136.582C144.497 140.163 137.857 141.953 130.5 141.953ZM209.113 140H186.457C185.936 140 185.676 139.674 185.676 139.023L186.066 1.62109C186.066 1.10026 186.327 0.839844 186.848 0.839844H227.277C234.504 0.839844 241.145 2.59766 247.199 6.11328C253.254 9.62891 258.072 14.349 261.652 20.2734C265.298 26.1979 267.121 32.9036 267.121 40.3906C267.121 45.2734 266.372 49.7005 264.875 53.6719C263.378 57.6432 261.62 60.9961 259.602 63.7305C257.648 66.4648 255.858 68.4831 254.23 69.7852C261.457 77.793 265.07 87.2005 265.07 98.0078L265.266 139.023C265.266 139.674 264.94 140 264.289 140H241.633C241.112 140 240.852 139.805 240.852 139.414V98.0078C240.852 93.1901 239.159 89.0234 235.773 85.5078C232.388 81.9922 228.221 80.2344 223.273 80.2344H210.09L209.895 139.023C209.895 139.674 209.634 140 209.113 140ZM227.277 24.7656H210.09V56.2109H227.277C231.379 56.2109 235.025 54.681 238.215 51.6211C241.47 48.5612 243.098 44.8177 243.098 40.3906C243.098 36.1589 241.535 32.513 238.41 29.4531C235.285 26.3281 231.574 24.7656 227.277 24.7656ZM303.938 140H283.918C282.876 140 282.355 139.544 282.355 138.633L282.16 2.40234C282.16 1.36068 282.681 0.839844 283.723 0.839844H301.789L335.578 79.6484L334.602 2.40234C334.602 1.36068 335.188 0.839844 336.359 0.839844H356.184C356.965 0.839844 357.355 1.36068 357.355 2.40234L357.551 138.828C357.551 139.609 357.225 140 356.574 140H338.996L304.328 66.3672L305.793 138.438C305.793 139.479 305.174 140 303.938 140Z"
          fill="url(#sidebar_grad)" />
        <defs>
          <linearGradient id="sidebar_grad" x1="476" y1="0" x2="0" y2="294" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#50D3FC" />
            <stop offset="45%" stop-color="#0A1FAB" />
            <stop offset="100%" stop-color="#FF2095" />
          </linearGradient>
        </defs>
      </svg>
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
        <span>Configure</span>
      </router-link>
      <router-link
        :to="{ name: 'TenantInsights', params: { tenantId: activeTenant.id } }"
        class="nav-item" active-class="nav-item--active"
      >
        <font-awesome-icon :icon="['fas', 'chart-line']" class="nav-item__icon" />
        <span>Insights</span>
      </router-link>
      <a
        :href="`/chat/${activeTenant.id}`"
        target="_blank"
        class="nav-item nav-item--external"
      >
        <font-awesome-icon :icon="['fas', 'comments']" class="nav-item__icon" />
        <span>{{ $t('sidebar.chatbot') }}</span>
        <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="nav-item__ext" />
      </a>
    </nav>

    <div class="sidebar__section-label">{{ $t('sidebar.account') }}</div>
    <nav class="sidebar__nav">
      <router-link to="/manage-tenants" class="nav-item" active-class="nav-item--active">
        <font-awesome-icon :icon="['fas', 'grid-2']" class="nav-item__icon" />
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
        <router-link to="/profile" class="footer-link">
          <font-awesome-icon :icon="['fas', 'user']" />
          {{ $t('sidebar.profile') }}
        </router-link>
        <router-link to="/subscription" class="footer-link">
          <font-awesome-icon :icon="['fas', 'credit-card']" />
          {{ $t('sidebar.subscription') }}
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
.sidebar {
  position: fixed;
  left: 0; top: 0; bottom: 0;
  width: var(--sidebar-width);
  background: var(--surface-1);
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
.sidebar__logo svg { max-width: 80px; }

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
  color: var(--surface-text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color var(--t-fast), background var(--t-fast);
  text-align: left;
}
.tenant-pill:hover { border-color: var(--brand-indigo); background: var(--surface-2); }

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
  box-shadow: var(--shadow-card);
}
.dropdown-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  font-size: 13px;
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
.dropdown-row--active { color: var(--brand-cyan); font-weight: 600; }
.dropdown-row--new { color: var(--surface-muted); font-size: 12px; }
.dropdown-row--new:hover { color: var(--surface-text); }
.dropdown-row__dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--surface-3);
  flex-shrink: 0;
}
.dropdown-row__dot--active { background: var(--brand-indigo); }
.dropdown-divider { height: 1px; background: var(--surface-3); margin: 2px 0; }

/* Dropdown transition */
.dropdown-enter-active, .dropdown-leave-active { transition: opacity 0.15s, transform 0.15s; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Section labels ────────────────────────────────── */
.sidebar__section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--surface-muted);
  padding: 12px 10px 4px;
}

/* ── Nav items ─────────────────────────────────────── */
.sidebar__nav { display: flex; flex-direction: column; gap: 1px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  font-size: 13.5px;
  font-weight: 500;
  color: var(--surface-muted);
  text-decoration: none;
  transition: color var(--t-fast), background var(--t-fast), transform var(--t-fast);
  position: relative;
}
.nav-item:hover {
  color: var(--surface-text);
  background: var(--surface-2);
  transform: translateX(2px);
}
.nav-item--active {
  color: var(--surface-heading);
  background: var(--gradient-brand-soft);
  font-weight: 600;
}
.nav-item--active::before {
  content: '';
  position: absolute;
  left: 0; top: 4px; bottom: 4px;
  width: 3px;
  background: var(--gradient-brand);
  border-radius: 0 2px 2px 0;
}
.nav-item__icon { width: 16px; color: inherit; flex-shrink: 0; }
.nav-item--active .nav-item__icon { color: var(--brand-cyan); }
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
  background: var(--gradient-brand);
  color: white;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-info { overflow: hidden; }
.user-info__name { font-size: 13px; font-weight: 600; color: var(--surface-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-info__email { font-size: 11px; color: var(--surface-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar__footer-links { display: flex; flex-direction: column; gap: 1px; }

.footer-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--surface-muted);
  text-decoration: none;
  cursor: pointer;
  transition: color var(--t-fast), background var(--t-fast);
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
}
.footer-link:hover { color: var(--surface-text); background: var(--surface-2); }
.footer-link--danger:hover { color: var(--status-error); background: rgba(255,68,68,0.08); }

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
    transform: translateX(-100%);
    transition: transform var(--t-normal);
    box-shadow: 8px 0 32px rgba(0,0,0,0.5);
  }
  .sidebar--mobile-open {
    transform: translateX(0);
  }
}
</style>
