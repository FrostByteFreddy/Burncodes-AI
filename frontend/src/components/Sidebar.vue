<template>
  <nav class="bc-sidebar" :aria-label="$t('sidebar.mainNav')">
    <router-link to="/manage-tenants" class="bc-sidebar__logo"><img src="/logo.svg" alt="Burncodes AI" /></router-link>

    <!-- Chatbot switcher -->
    <div ref="switcherRef" class="bc-switcher">
      <button type="button" class="bc-switcher__btn" aria-haspopup="listbox" :aria-expanded="switcherOpen ? 'true' : 'false'" @click="switcherOpen = !switcherOpen">
        <span :class="['bc-switcher__dot', isOn(activeTenant) ? 'is-on' : 'is-off']" aria-hidden="true"></span>
        <span class="bc-switcher__text">
          <span class="bc-switcher__name">{{ activeTenant?.name ?? $t('sidebar.selectTenant') }}</span>
          <span v-if="activeTenant" class="bc-switcher__state">{{ isOn(activeTenant) ? $t('ui.status.on') : $t('ui.status.off') }}</span>
        </span>
        <BcIcon name="chevron-down" class="bc-switcher__chev" />
      </button>
      <div v-if="switcherOpen" class="bc-popover bc-switcher__menu" role="listbox">
        <div v-for="t in tenantsStore.tenants" :key="t.id" role="option" tabindex="0" :aria-selected="t.id === activeTenant?.id ? 'true' : 'false'"
          :class="['bc-switcher__opt', { 'is-current': t.id === activeTenant?.id }]" @click="selectTenant(t)" @keydown.enter="selectTenant(t)">
          <span :class="['bc-switcher__dot', isOn(t) ? 'is-on' : 'is-off']" aria-hidden="true"></span>
          <span>{{ t.name }}</span>
          <BcIcon v-if="t.id === activeTenant?.id" name="check" />
        </div>
        <div class="bc-switcher__sep"></div>
        <div class="bc-switcher__opt" role="option" tabindex="0" @click="newTenant" @keydown.enter="newTenant">
          <BcIcon name="plus" />{{ $t('manageTenants.newTenant') }}
        </div>
        <router-link to="/manage-tenants" class="bc-switcher__opt" role="option" @click="switcherOpen = false">
          <BcIcon name="list" />{{ $t('ui.allBots') }}
        </router-link>
      </div>
    </div>

    <template v-if="activeTenant">
      <div class="bc-nav__section">{{ $t('sidebar.workspace') }}</div>
      <router-link v-for="item in NAV" :key="item.route" :to="{ name: item.route, params: { tenantId: activeTenant.id } }"
        class="bc-nav__item" active-class="is-active" @click="$emit('navigate')">
        <BcIcon :name="item.icon" class="bc-nav__icon" />
        <span class="bc-nav__label">{{ $t(item.label) }}</span>
      </router-link>
      <div class="bc-nav__row">
        <router-link :to="{ name: 'TenantTestPage', params: { tenantId: activeTenant.id } }" class="bc-nav__item" active-class="is-active" @click="$emit('navigate')">
          <BcIcon name="arrow-up-right-from-square" class="bc-nav__icon" />
          <span class="bc-nav__label">{{ $t('sidebar.chatbot') }}</span>
          <BcIcon v-if="activeTenant.test_protected" name="lock" :label="$t('testPage.link.protected')" />
        </router-link>
        <BcIconButton icon="link" size="sm" :label="linkCopied ? $t('sidebar.linkCopied') : $t('sidebar.copyLink')" @click="copyLink" />
      </div>
    </template>

    <div class="bc-nav__section">{{ $t('sidebar.account') }}</div>
    <router-link to="/manage-tenants" class="bc-nav__item" active-class="is-active" @click="$emit('navigate')">
      <BcIcon name="layer-group" class="bc-nav__icon" />
      <span class="bc-nav__label">{{ $t('sidebar.manageTenants') }}</span>
    </router-link>

    <div class="bc-sidebar__spacer"></div>
    <div class="bc-sidebar__user">
      <span class="bc-avatar" aria-hidden="true">{{ initials }}</span>
      <span class="bc-sidebar__who">
        <span class="bc-sidebar__name">{{ userName }}</span>
        <span class="bc-sidebar__email">{{ authStore.user?.email }}</span>
      </span>
    </div>
    <router-link :to="{ name: 'AccountSettings', params: { section: 'profile' } }" :class="['bc-nav__item', { 'is-active': route.name === 'AccountSettings' }]" @click="$emit('navigate')">
      <BcIcon name="gear" class="bc-nav__icon" />
      <span class="bc-nav__label">{{ $t('sidebar.settings') }}</span>
    </router-link>
    <a href="#" class="bc-nav__item" @click.prevent="handleLogout">
      <BcIcon name="arrow-right-from-bracket" class="bc-nav__icon" />
      <span class="bc-nav__label">{{ $t('sidebar.logout') }}</span>
    </a>
  </nav>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTenantsStore } from '../stores/tenants';
import { useAuthStore } from '../stores/auth';
import { BcIcon, BcIconButton } from './ui';

const emit = defineEmits(['newTenant', 'navigate']);

// The design system's fixed icon per area
const NAV = [
  { route: 'TenantOverview', label: 'sidebar.overview', icon: 'house' },
  { route: 'TenantSources', label: 'sidebar.sources', icon: 'book-open' },
  { route: 'TenantConfigure', label: 'sidebar.configure', icon: 'sliders' },
  { route: 'TenantInsights', label: 'sidebar.insights', icon: 'chart-column' },
  { route: 'TenantInstall', label: 'sidebar.install', icon: 'code' },
  { route: 'TenantSettings', label: 'sidebar.botSettings', icon: 'screwdriver-wrench' },
];

const tenantsStore = useTenantsStore();
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const activeTenant = computed(() => tenantsStore.currentTenant);
const isOn = (t) => Boolean(t) && t.is_active !== false;

const userName = computed(() => {
  const meta = authStore.user?.user_metadata;
  if (meta?.first_name) return `${meta.first_name} ${meta.last_name || ''}`.trim();
  return authStore.user?.email?.split('@')[0] || '';
});
const initials = computed(() => userName.value.split(/\s+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase() || '?');

// ── Switcher ────────────────────────────────────────────────────────
const switcherOpen = ref(false);
const switcherRef = ref(null);
const selectTenant = (t) => {
  switcherOpen.value = false;
  tenantsStore.selectTenant(t);
  router.push({ name: 'TenantOverview', params: { tenantId: t.id } });
  emit('navigate');
};
const newTenant = () => { switcherOpen.value = false; emit('newTenant'); };
const onOutside = (e) => { if (switcherRef.value && !switcherRef.value.contains(e.target)) switcherOpen.value = false; };

// ── Public test page link ───────────────────────────────────────────
const linkCopied = ref(false);
async function copyLink() {
  try {
    await navigator.clipboard.writeText(`${window.location.origin}/chat/${activeTenant.value.id}`);
    linkCopied.value = true;
    setTimeout(() => { linkCopied.value = false; }, 2000);
  } catch { /* the page itself offers the link to select by hand */ }
}

const handleLogout = async () => {
  await authStore.logout();
  router.push('/login');
};

onMounted(() => {
  tenantsStore.fetchTenants();
  document.addEventListener('click', onOutside);
});
onUnmounted(() => document.removeEventListener('click', onOutside));

// The address names the chatbot; with only one, it's the one
watch(
  () => [tenantsStore.tenants, route.params.tenantId],
  ([tenants, tenantId]) => {
    if (tenantId) {
      const t = tenants.find((x) => x.id === tenantId);
      if (t) tenantsStore.selectTenant(t);
    } else if (tenants.length === 1) {
      tenantsStore.selectTenant(tenants[0]);
    }
  },
  { immediate: true, deep: true },
);
</script>
