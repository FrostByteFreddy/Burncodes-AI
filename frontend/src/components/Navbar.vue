<template>
  <header class="sticky top-0 z-50 bg-base-100/95 backdrop-blur border-b border-base-300">
    <div class="flex items-center justify-between px-4 md:px-8 h-16">

      <!-- Left: Logo + Tenant Switcher -->
      <div class="flex items-center gap-4">
        <router-link to="/manage-tenants" class="shrink-0 flex items-center">
          <svg width="90" height="36" viewBox="0 0 476 294" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M37.5312 140H1.69141C1.17057 140 0.910156 139.674 0.910156 139.023L1.30078 1.62109C1.30078 1.10026 1.5612 0.839844 2.08203 0.839844H40.5586C48.0456 0.839844 54.849 2.66276 60.9688 6.30859C66.9583 9.95443 71.6784 14.8047 75.1289 20.8594C78.5794 26.849 80.3047 33.3594 80.3047 40.3906C80.3047 46.1198 79.0026 51.4583 76.3984 56.4062C73.7943 61.3542 70.7018 65.3581 67.1211 68.418C70.9622 72.2591 73.957 76.7188 76.1055 81.7969C78.2539 86.875 79.3281 92.2135 79.3281 97.8125C79.3281 105.56 77.4727 112.624 73.7617 119.004C69.9857 125.384 64.9401 130.495 58.625 134.336C52.3099 138.112 45.2786 140 37.5312 140ZM40.5586 24.5703H25.3242V56.0156H40.5586C45.181 56.0156 48.9245 54.388 51.7891 51.1328C54.6536 47.8125 56.0859 44.2318 56.0859 40.3906C56.0859 36.1589 54.556 32.4805 51.4961 29.3555C48.4362 26.1654 44.7904 24.5703 40.5586 24.5703ZM37.5312 80.2344H25.3242L25.1289 115.586H37.5312C42.349 115.586 46.4831 113.828 49.9336 110.312C53.3841 106.797 55.1094 102.63 55.1094 97.8125C55.1094 92.9948 53.3841 88.8607 49.9336 85.4102C46.4831 81.9596 42.349 80.2344 37.5312 80.2344ZM130.5 141.953C123.469 141.953 116.958 140.13 110.969 136.484C104.979 132.839 100.194 127.956 96.6133 121.836C93.0977 115.651 91.3398 108.913 91.3398 101.621L91.7305 1.62109C91.7305 1.10026 91.9909 0.839844 92.5117 0.839844H114.973C115.493 0.839844 115.754 1.10026 115.754 1.62109V101.621C115.754 106.113 117.186 109.954 120.051 113.145C122.915 116.27 126.398 117.832 130.5 117.832C134.797 117.832 138.378 116.27 141.242 113.145C144.107 109.954 145.539 106.113 145.539 101.621V1.62109C145.539 1.10026 145.799 0.839844 146.32 0.839844H168.781C169.302 0.839844 169.562 1.10026 169.562 1.62109L169.953 101.621C169.953 108.978 168.195 115.749 164.68 121.934C161.099 128.053 156.346 132.936 150.422 136.582C144.497 140.163 137.857 141.953 130.5 141.953ZM209.113 140H186.457C185.936 140 185.676 139.674 185.676 139.023L186.066 1.62109C186.066 1.10026 186.327 0.839844 186.848 0.839844H227.277C234.504 0.839844 241.145 2.59766 247.199 6.11328C253.254 9.62891 258.072 14.349 261.652 20.2734C265.298 26.1979 267.121 32.9036 267.121 40.3906C267.121 45.2734 266.372 49.7005 264.875 53.6719C263.378 57.6432 261.62 60.9961 259.602 63.7305C257.648 66.4648 255.858 68.4831 254.23 69.7852C261.457 77.793 265.07 87.2005 265.07 98.0078L265.266 139.023C265.266 139.674 264.94 140 264.289 140H241.633C241.112 140 240.852 139.805 240.852 139.414V98.0078C240.852 93.1901 239.159 89.0234 235.773 85.5078C232.388 81.9922 228.221 80.2344 223.273 80.2344H210.09L209.895 139.023C209.895 139.674 209.634 140 209.113 140ZM227.277 24.7656H210.09V56.2109H227.277C231.379 56.2109 235.025 54.681 238.215 51.6211C241.47 48.5612 243.098 44.8177 243.098 40.3906C243.098 36.1589 241.535 32.513 238.41 29.4531C235.285 26.3281 231.574 24.7656 227.277 24.7656ZM303.938 140H283.918C282.876 140 282.355 139.544 282.355 138.633L282.16 2.40234C282.16 1.36068 282.681 0.839844 283.723 0.839844H301.789L335.578 79.6484L334.602 2.40234C334.602 1.36068 335.188 0.839844 336.359 0.839844H356.184C356.965 0.839844 357.355 1.36068 357.355 2.40234L357.551 138.828C357.551 139.609 357.225 140 356.574 140H338.996L304.328 66.3672L305.793 138.438C305.793 139.479 305.174 140 303.938 140Z"
              fill="url(#navbar_gradient)" />
            <defs>
              <linearGradient id="navbar_gradient" x1="590" y1="351.5" x2="1.50003" y2="-15.5" gradientUnits="userSpaceOnUse">
                <stop offset="0.108063" stop-color="#50D3FC" />
                <stop offset="0.41582" stop-color="#0A1FAB" />
                <stop offset="0.86963" stop-color="#FF2095" />
              </linearGradient>
            </defs>
          </svg>
        </router-link>

        <!-- Tenant switcher (only when multiple tenants) -->
        <div v-if="tenantsStore.tenants.length > 1" class="relative" ref="tenantDropdownRef">
          <button
            @click="tenantDropdownOpen = !tenantDropdownOpen"
            class="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md bg-base-200 hover:bg-base-300 transition-colors"
          >
            <span class="max-w-[120px] truncate">{{ activeTenant ? activeTenant.name : $t('sidebar.selectTenant') }}</span>
            <font-awesome-icon :icon="['fas', 'chevron-down']" class="w-3 h-3 opacity-60" />
          </button>
          <div
            v-show="tenantDropdownOpen"
            class="absolute left-0 top-full mt-1 w-48 py-1 bg-base-100 border border-base-300 rounded-lg shadow-lg z-50"
          >
            <a
              v-for="tenant in tenantsStore.tenants"
              :key="tenant.id"
              @click="selectTenant(tenant)"
              href="#"
              class="block px-4 py-2 text-sm hover:bg-base-200 transition-colors"
              :class="tenant.id === activeTenant?.id ? 'text-primary font-medium' : 'text-base-content'"
            >
              {{ tenant.name }}
            </a>
          </div>
        </div>
        <!-- Single tenant name badge -->
        <span v-else-if="tenantsStore.tenants.length === 1" class="text-sm font-medium text-base-content/70 hidden sm:inline">
          {{ tenantsStore.tenants[0].name }}
        </span>
      </div>

      <nav v-if="activeTenant" class="hidden lg:flex items-center gap-2">
        <router-link
          :to="{ name: 'TenantSources', params: { tenantId: activeTenant.id } }"
          class="nav-link"
          active-class="nav-link-active"
        >
          {{ $t('sidebar.sources') }}
        </router-link>
        <router-link
          :to="{ name: 'TenantSettings', params: { tenantId: activeTenant.id } }"
          class="nav-link"
          active-class="nav-link-active"
        >
          {{ $t('sidebar.configuration') }}
        </router-link>
        <router-link
          :to="{ name: 'TenantFineTune', params: { tenantId: activeTenant.id } }"
          class="nav-link"
          active-class="nav-link-active"
        >
          {{ $t('sidebar.fineTune') }}
        </router-link>
        <router-link
          :to="{ name: 'Analytics', params: { tenantId: activeTenant.id } }"
          class="nav-link"
          active-class="nav-link-active"
        >
          {{ $t('sidebar.analytics') }}
        </router-link>
        <router-link
          :to="{ name: 'ChatLogs', params: { tenantId: activeTenant.id } }"
          class="nav-link"
          active-class="nav-link-active"
        >
          {{ $t('sidebar.chatLogs') }}
        </router-link>
        <a
          :href="`/chat/${activeTenant.id}`"
          target="_blank"
          class="nav-link"
        >
          {{ $t('sidebar.chatbot') }}
          <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="w-2.5 h-2.5 opacity-40" />
        </a>
      </nav>

      <!-- Right: User menu + mobile hamburger -->
      <div class="flex items-center gap-2">
        <!-- User dropdown (desktop) -->
        <div class="relative hidden md:block" ref="userDropdownRef">
          <button
            @click="userDropdownOpen = !userDropdownOpen"
            class="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-base-200 transition-colors text-sm"
          >
            <div class="w-7 h-7 rounded-full bg-primary/15 flex items-center justify-center text-primary font-semibold text-xs shrink-0">
              {{ userInitial }}
            </div>
            <font-awesome-icon :icon="['fas', 'chevron-down']" class="w-3 h-3 opacity-60" />
          </button>
          <div
            v-show="userDropdownOpen"
            class="absolute right-0 top-full mt-1 w-48 py-1 bg-base-100 border border-base-300 rounded-lg shadow-lg z-50"
          >
            <div class="px-4 py-2 border-b border-base-200 mb-1">
              <p class="text-xs text-base-content/50 truncate">{{ authStore.user?.email }}</p>
            </div>
            <router-link to="/profile" @click="userDropdownOpen = false" class="dropdown-item">
              <font-awesome-icon :icon="['fas', 'user']" class="w-4 h-4" />
              {{ $t('sidebar.profile') }}
            </router-link>
            <router-link to="/manage-tenants" @click="userDropdownOpen = false" class="dropdown-item">
              <font-awesome-icon :icon="['fas', 'list-check']" class="w-4 h-4" />
              {{ $t('sidebar.manageTenants') }}
            </router-link>
            <router-link to="/subscription" @click="userDropdownOpen = false" class="dropdown-item">
              <font-awesome-icon :icon="['fas', 'credit-card']" class="w-4 h-4" />
              {{ $t('sidebar.subscription') }}
            </router-link>
            <div class="border-t border-base-200 mt-1 pt-1">
              <button @click="handleLogout" class="dropdown-item w-full text-left text-error">
                <font-awesome-icon :icon="['fas', 'arrow-right-from-bracket']" class="w-4 h-4" />
                {{ $t('sidebar.logout') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Mobile hamburger -->
        <button
          @click="mobileMenuOpen = !mobileMenuOpen"
          class="lg:hidden btn btn-ghost btn-sm btn-square"
          aria-label="Toggle menu"
        >
          <font-awesome-icon :icon="mobileMenuOpen ? ['fas', 'xmark'] : ['fas', 'bars']" class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Mobile drawer -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-if="mobileMenuOpen" class="lg:hidden border-t border-base-300 bg-base-100 px-4 py-4 space-y-1">
        <!-- Tenant links -->
        <template v-if="activeTenant">
          <p class="text-xs font-semibold uppercase tracking-wider text-base-content/40 px-2 mb-2">{{ activeTenant.name }}</p>
          <router-link :to="{ name: 'TenantSources', params: { tenantId: activeTenant.id } }" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'database']" class="w-4 h-4" /> {{ $t('sidebar.sources') }}
          </router-link>
          <router-link :to="{ name: 'TenantSettings', params: { tenantId: activeTenant.id } }" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'sliders']" class="w-4 h-4" /> {{ $t('sidebar.configuration') }}
          </router-link>
          <router-link :to="{ name: 'TenantFineTune', params: { tenantId: activeTenant.id } }" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'flask-vial']" class="w-4 h-4" /> {{ $t('sidebar.fineTune') }}
          </router-link>
          <router-link :to="{ name: 'Analytics', params: { tenantId: activeTenant.id } }" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'chart-line']" class="w-4 h-4" /> {{ $t('sidebar.analytics') }}
          </router-link>
          <router-link :to="{ name: 'ChatLogs', params: { tenantId: activeTenant.id } }" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'history']" class="w-4 h-4" /> {{ $t('sidebar.chatLogs') }}
          </router-link>
          <a :href="`/chat/${activeTenant.id}`" target="_blank" class="mobile-link">
            <font-awesome-icon :icon="['fas', 'comments']" class="w-4 h-4" /> {{ $t('sidebar.chatbot') }}
          </a>
        </template>

        <!-- User section -->
        <div class="border-t border-base-200 mt-3 pt-3 space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-base-content/40 px-2 mb-2">{{ $t('sidebar.settings') }}</p>
          <router-link to="/profile" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'user']" class="w-4 h-4" /> {{ $t('sidebar.profile') }}
          </router-link>
          <router-link to="/manage-tenants" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'list-check']" class="w-4 h-4" /> {{ $t('sidebar.manageTenants') }}
          </router-link>
          <router-link to="/subscription" class="mobile-link" @click="mobileMenuOpen = false">
            <font-awesome-icon :icon="['fas', 'credit-card']" class="w-4 h-4" /> {{ $t('sidebar.subscription') }}
          </router-link>
          <button @click="handleLogout" class="mobile-link w-full text-left text-error">
            <font-awesome-icon :icon="['fas', 'arrow-right-from-bracket']" class="w-4 h-4" /> {{ $t('sidebar.logout') }}
          </button>
        </div>
      </div>
    </transition>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useAuthStore } from '../stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const tenantsStore = useTenantsStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const tenantDropdownOpen = ref(false)
const userDropdownOpen = ref(false)
const mobileMenuOpen = ref(false)
const tenantDropdownRef = ref(null)
const userDropdownRef = ref(null)

const activeTenant = computed(() => tenantsStore.currentTenant)

const userInitial = computed(() => {
  const email = authStore.user?.email || ''
  const meta = authStore.user?.user_metadata
  if (meta?.first_name) return meta.first_name[0].toUpperCase()
  return email[0]?.toUpperCase() || '?'
})

onMounted(() => {
  tenantsStore.fetchTenants()
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})

const handleOutsideClick = (e) => {
  if (tenantDropdownRef.value && !tenantDropdownRef.value.contains(e.target)) {
    tenantDropdownOpen.value = false
  }
  if (userDropdownRef.value && !userDropdownRef.value.contains(e.target)) {
    userDropdownOpen.value = false
  }
}

watch(
  () => [tenantsStore.tenants, route.params.tenantId],
  ([newTenants, tenantId]) => {
    if (tenantId) {
      const tenant = newTenants.find((t) => t.id === tenantId)
      if (tenant) tenantsStore.selectTenant(tenant)
    } else if (newTenants.length === 1) {
      tenantsStore.selectTenant(newTenants[0])
    }
  },
  { immediate: true, deep: true }
)

const selectTenant = (tenant) => {
  tenantDropdownOpen.value = false
  router.push({ name: 'TenantSettings', params: { tenantId: tenant.id } })
}

const handleLogout = async () => {
  userDropdownOpen.value = false
  mobileMenuOpen.value = false
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.375rem;
  transition: background-color 0.15s, color 0.15s;
  color: oklch(var(--bc) / 0.65);
  letter-spacing: 0.01em;
}
.nav-link:hover {
  background-color: oklch(var(--b2));
  color: oklch(var(--bc));
}
.nav-link-active {
  background-color: oklch(var(--b2));
  color: oklch(var(--bc));
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  transition: background-color 0.15s;
  color: oklch(var(--bc));
}
.dropdown-item:hover {
  background-color: oklch(var(--b2));
}
.mobile-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
  border-radius: 0.375rem;
  transition: background-color 0.15s;
  color: oklch(var(--bc));
}
.mobile-link:hover {
  background-color: oklch(var(--b2));
}
</style>
