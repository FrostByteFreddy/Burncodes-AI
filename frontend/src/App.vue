<template>
  <div class="app-root">
    <!-- Sidebar layout (authenticated routes) -->
    <template v-if="layout === 'default'">
      <!-- Mobile top bar -->
      <header class="mobile-topbar">
        <button class="mobile-topbar__menu" @click="mobileOpen = !mobileOpen" aria-label="Menu">
          <font-awesome-icon :icon="mobileOpen ? ['fas', 'xmark'] : ['fas', 'bars']" />
        </button>
        <router-link to="/manage-tenants" class="mobile-topbar__logo">
          <img src="@/assets/logo.png" alt="Logo" style="height:28px;width:auto;" />
        </router-link>
      </header>

      <div class="app-shell" id="app-layout">
        <Sidebar
          :mobile-open="mobileOpen"
          @new-tenant="showCreateModal = true"
          @close-mobile="mobileOpen = false"
        />
        <main class="app-main" :class="{ 'has-chat': route.name === 'Chat' }">
          <router-view />
        </main>
      </div>
    </template>

    <!-- Blank layout: Login, Signup, Chat -->
    <template v-else>
      <router-view />
    </template>

    <ToastContainer />
    <SessionExpiredModal v-if="authStore.sessionExpired" />
    <CreateTenantModal v-if="showCreateModal" @close="showCreateModal = false" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import ToastContainer from './components/ToastContainer.vue'
import SessionExpiredModal from './components/SessionExpiredModal.vue'
import CreateTenantModal from './components/CreateTenantModal.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const mobileOpen = ref(false)
const showCreateModal = ref(false)

const layout = computed(() => {
  const blank = ['Login', 'Signup', 'Chat']
  // Default to blank while route is unresolved to prevent sidebar flash
  return (!route.name || blank.includes(route.name)) ? 'blank' : 'default'
})
</script>

<style>
@import './assets/design-tokens.css';
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  background: var(--surface-0);
  color: var(--surface-text);
  -webkit-font-smoothing: antialiased;
}

.app-root { min-height: 100vh; }

.app-shell {
  display: flex;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  overflow-y: auto;
  padding: 32px 40px;
}

.app-main.has-chat {
  padding: 0;
  overflow: hidden;
}

/* Mobile top bar (hidden on desktop) */
.mobile-topbar {
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 56px;
  background: var(--surface-1);
  border-bottom: 1px solid var(--surface-3);
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 101;
}
.mobile-topbar__menu {
  background: none;
  border: none;
  color: var(--surface-text);
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-sm);
}
.mobile-topbar__menu:hover { background: var(--surface-2); }

@media (max-width: 768px) {
  .mobile-topbar { display: flex; }
  .app-main {
    margin-left: 0;
    padding: 80px 20px 24px;
  }
}
</style>