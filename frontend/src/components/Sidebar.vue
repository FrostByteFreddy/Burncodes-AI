<template>
  <Sidebar :collapsible="isMobile ? 'offcanvas' : 'none'" :aria-label="$t('sidebar.mainNav')"
    :class="isMobile ? '' : 'sticky top-0 h-svh border-x'">
    <SidebarHeader class="gap-3 p-3">
      <router-link to="/manage-tenants" class="px-2 pt-2 pb-1"><img src="/logo.svg" alt="Burncodes AI" class="h-9 w-auto" /></router-link>

      <!-- Chatbot switcher -->
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <SidebarMenuButton size="lg" variant="outline">
            <span :class="cn('size-2.5 shrink-0 rounded-full', isOn(activeTenant) ? 'bg-success' : 'bg-muted-foreground')" aria-hidden="true"></span>
            <span class="grid min-w-0 flex-1 leading-tight">
              <span class="truncate font-bold">{{ activeTenant?.name ?? $t('sidebar.selectTenant') }}</span>
              <span v-if="activeTenant" class="truncate text-sm font-normal text-muted-foreground">{{ isOn(activeTenant) ? $t('ui.status.on') : $t('ui.status.off') }}</span>
            </span>
            <BcIcon name="chevron-down" />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" class="w-(--reka-dropdown-menu-trigger-width) min-w-56">
          <DropdownMenuGroup>
            <DropdownMenuItem v-for="t in tenantsStore.tenants" :key="t.id" @select="selectTenant(t)">
              <span :class="cn('size-2.5 shrink-0 rounded-full', isOn(t) ? 'bg-success' : 'bg-muted-foreground')" aria-hidden="true"></span>
              <span class="flex-1 truncate">{{ t.name }}</span>
              <BcIcon v-if="t.id === activeTenant?.id" name="check" />
            </DropdownMenuItem>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuItem @select="newTenant"><BcIcon name="plus" />{{ $t('manageTenants.newTenant') }}</DropdownMenuItem>
            <DropdownMenuItem as-child><router-link to="/manage-tenants" @click="closeMobile"><BcIcon name="list" />{{ $t('ui.allBots') }}</router-link></DropdownMenuItem>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarHeader>

    <SidebarContent>
      <SidebarGroup v-if="activeTenant">
        <SidebarGroupLabel>{{ $t('sidebar.workspace') }}</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="item in NAV" :key="item.route">
              <SidebarMenuButton as-child :is-active="isActive({ name: item.route, params: { tenantId: activeTenant.id } })">
                <router-link :to="{ name: item.route, params: { tenantId: activeTenant.id } }" @click="closeMobile">
                  <BcIcon :name="item.icon" /><span>{{ $t(item.label) }}</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton as-child :is-active="isActive({ name: 'TenantTestPage', params: { tenantId: activeTenant.id } })">
                <router-link :to="{ name: 'TenantTestPage', params: { tenantId: activeTenant.id } }" @click="closeMobile">
                  <BcIcon name="arrow-up-right-from-square" />
                  <span>{{ $t('sidebar.chatbot') }}</span>
                  <BcIcon v-if="activeTenant.test_protected" name="lock" :label="$t('testPage.link.protected')" />
                </router-link>
              </SidebarMenuButton>
              <SidebarMenuAction :title="linkCopied ? $t('sidebar.linkCopied') : $t('sidebar.copyLink')" :aria-label="linkCopied ? $t('sidebar.linkCopied') : $t('sidebar.copyLink')" @click="copyLink">
                <BcIcon :name="linkCopied ? 'check' : 'link'" />
              </SidebarMenuAction>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <SidebarGroup>
        <SidebarGroupLabel>{{ $t('sidebar.account') }}</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton as-child :is-active="route.name === 'ManageTenants'">
                <router-link to="/manage-tenants" @click="closeMobile"><BcIcon name="layer-group" /><span>{{ $t('sidebar.manageTenants') }}</span></router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>

    <SidebarSeparator class="mx-3" />
    <SidebarFooter class="p-3">
      <div class="flex items-center gap-3 px-2 py-2">
        <Avatar><AvatarFallback>{{ initials }}</AvatarFallback></Avatar>
        <span class="grid min-w-0 leading-tight">
          <span class="truncate font-semibold">{{ userName }}</span>
          <span class="truncate text-sm text-muted-foreground">{{ authStore.user?.email }}</span>
        </span>
      </div>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton as-child :is-active="route.name === 'AccountSettings'">
            <router-link :to="{ name: 'AccountSettings', params: { section: 'profile' } }" @click="closeMobile"><BcIcon name="gear" /><span>{{ $t('sidebar.settings') }}</span></router-link>
          </SidebarMenuButton>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <SidebarMenuButton @click="handleLogout"><BcIcon name="arrow-right-from-bracket" /><span>{{ $t('sidebar.logout') }}</span></SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  </Sidebar>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTenantsStore } from '../stores/tenants';
import { useAuthStore } from '../stores/auth';
import { cn } from '@/lib/utils';
import { BcIcon } from './ui';
import { Avatar, AvatarFallback } from './ui/avatar';
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from './ui/dropdown-menu';
import { Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader, SidebarMenu, SidebarMenuAction, SidebarMenuButton, SidebarMenuItem, SidebarSeparator, useSidebar } from './ui/sidebar';

const emit = defineEmits(['newTenant']);
const { isMobile, setOpenMobile } = useSidebar();
const closeMobile = () => setOpenMobile(false);

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

// The current area stays marked on its sub-pages (a crawl under Wissen)
const isActive = (to) => route.path.startsWith(router.resolve(to).path);

// ── Switcher ────────────────────────────────────────────────────────
const selectTenant = (t) => {
  tenantsStore.selectTenant(t);
  router.push({ name: 'TenantOverview', params: { tenantId: t.id } });
  closeMobile();
};
const newTenant = () => { closeMobile(); emit('newTenant'); };

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

onMounted(() => tenantsStore.fetchTenants());

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
