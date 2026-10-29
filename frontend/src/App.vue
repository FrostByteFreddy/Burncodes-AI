<template>
  <div class="app-root">
    <!-- Dashboard: sidebar + centred content -->
    <div v-if="layout === 'default'" :class="['bc-shell', { 'is-menu-open': mobileOpen }]">
      <div class="bc-shell__top">
        <BcIconButton :icon="mobileOpen ? 'xmark' : 'bars'" :label="$t('ui.menu')" @click="mobileOpen = !mobileOpen" />
        <router-link to="/manage-tenants"><img src="/logo.svg" alt="Burncodes AI" class="bc-shell__toplogo" /></router-link>
      </div>
      <div class="bc-shell__side">
        <Sidebar @new-tenant="showCreateModal = true; mobileOpen = false" @navigate="mobileOpen = false" />
      </div>
      <div v-if="mobileOpen" class="app-scrim" @click="mobileOpen = false"></div>
      <main class="bc-shell__main">
        <div class="bc-shell__content"><router-view /></div>
      </main>
    </div>

    <!-- Blank layout: Login, Signup, Chat -->
    <template v-else>
      <router-view />
    </template>

    <ToastContainer :with-sidebar="layout === 'default'" />
    <SessionExpiredModal v-if="authStore.sessionExpired" />
    <CreateTenantModal v-if="showCreateModal" @close="showCreateModal = false" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import { BcIconButton } from './components/ui'
import ToastContainer from './components/ToastContainer.vue'
import SessionExpiredModal from './components/SessionExpiredModal.vue'
import CreateTenantModal from './components/CreateTenantModal.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const mobileOpen = ref(false)
const showCreateModal = ref(false)

const layout = computed(() => {
  const blank = ['Login', 'Signup', 'Chat', 'Share']
  // Default to blank while route is unresolved to prevent sidebar flash
  return (!route.name || blank.includes(route.name)) ? 'blank' : 'default'
})
</script>

<style>
@import './assets/tokens.css';
@import './assets/design-tokens.css';
@import './assets/bc.css';

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

a { color: var(--text-link); text-underline-offset: 2px; }
a:hover { color: var(--interactive-hover); }

/* One visible focus style everywhere (keyboard only) */
:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }

::selection { background: var(--interactive-soft); color: var(--text-primary); }

.app-root { min-height: 100vh; }
/* Sidebar and content form one centred column, so wide screens get even
   margins on both sides instead of everything hugging the left edge */
.bc-shell { min-height: 100vh; max-width: var(--shell-max); margin: 0 auto; }
@media (min-width: 1101px) {
  .bc-shell__side { border-left: 1px solid var(--border-subtle); }
}

/* The shell's sidebar is sticky on wide screens and slides in from the menu button below 1100px */
.bc-shell__side { position: sticky; top: 0; height: 100vh; overflow-y: auto; }
.app-scrim { display: none; }
/* The brand pages' (login, sign-up, onboarding) primary button: the logo's gradient.
   The dashboard never uses it. */
.bc-btn--brand { border: none; color: #fff; background: linear-gradient(135deg, var(--brand-indigo) 0%, var(--brand-magenta) 100%); }
.bc-btn--brand:hover:not(:disabled) { filter: brightness(1.08); }
.bc-btn--brand:disabled { background: var(--surface-2); color: var(--text-disabled); }

/* nav items fill the width of their row, not the height of the sidebar */
.bc-sidebar > .bc-nav__item { flex: none; }
.bc-sidebar__logo img { width: auto; }
@media (max-width: 1100px) {
  .bc-shell.is-menu-open .bc-shell__side {
    display: block; position: fixed; top: 56px; left: 0; bottom: 0; height: auto;
    z-index: var(--z-overlay); box-shadow: var(--shadow-3);
  }
  .bc-shell.is-menu-open .app-scrim { display: block; position: fixed; inset: 56px 0 0; background: var(--scrim); z-index: calc(var(--z-overlay) - 1); }
}
</style>