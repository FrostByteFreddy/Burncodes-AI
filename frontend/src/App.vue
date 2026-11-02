<template>
  <div class="app-root">
    <!-- Dashboard: sidebar + content, one centred column on wide screens -->
    <SidebarProvider v-if="layout === 'default'" :style="{ '--sidebar-width': '272px' }" class="mx-auto max-w-(--shell-max)">
      <AppSidebar @new-tenant="showCreateModal = true" />
      <SidebarInset class="min-w-0 bg-background">
        <header class="sticky top-0 z-10 flex h-14 items-center gap-3 bg-sidebar px-3 text-sidebar-foreground min-[1101px]:hidden">
          <SidebarTrigger :aria-label="$t('ui.menu')" class="text-white hover:bg-white/15 hover:text-white" />
          <router-link to="/manage-tenants"><img src="/logo_white.svg" alt="Burncodes AI" class="h-7" /></router-link>
        </header>
        <div class="p-6 min-[1101px]:p-10">
          <div class="mx-auto max-w-(--content-max)"><router-view /></div>
        </div>
      </SidebarInset>
    </SidebarProvider>

    <!-- Blank layout: Login, Signup, Chat -->
    <template v-else>
      <router-view />
    </template>

    <Toaster />
    <SessionExpiredModal v-if="authStore.sessionExpired" />
    <CreateTenantModal v-if="showCreateModal" @close="showCreateModal = false" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './components/Sidebar.vue'
import { SidebarInset, SidebarProvider, SidebarTrigger } from './components/ui/sidebar'
import { Toaster } from './components/ui/sonner'
import SessionExpiredModal from './components/SessionExpiredModal.vue'
import CreateTenantModal from './components/CreateTenantModal.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const showCreateModal = ref(false)

const layout = computed(() => {
  const blank = ['Login', 'Signup', 'Chat', 'Share', 'Onboarding']
  // Default to blank while route is unresolved to prevent sidebar flash
  return (!route.name || blank.includes(route.name)) ? 'blank' : 'default'
})
</script>

<style>
@import './assets/tokens.css';
@import './assets/design-tokens.css';
@import './assets/bc.css';

/* In a layer: unlayered rules would outrank every Tailwind utility */
@layer base {
  *, *::before, *::after { box-sizing: border-box; margin: 0; }

  body {
    font-family: var(--font-sans);
    font-size: 16px;
    line-height: 24px;
    background: var(--surface-0);
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
    -webkit-font-smoothing: antialiased;
  }

  h1, h2, h3, h4 { color: var(--text-primary); line-height: var(--leading-tight); font-weight: 700; }

  a:not([data-slot]) { color: var(--text-link); text-underline-offset: 2px; }
  a:not([data-slot]):hover { color: var(--interactive-hover); }
  p a:not([data-slot]) { text-decoration: underline; }

  /* One visible focus style everywhere (keyboard only) */
  :focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }

  ::selection { background: var(--interactive-soft); color: var(--text-primary); }
}

.app-root { min-height: 100vh; }
</style>