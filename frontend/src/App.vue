<template>
  <div id="app-layout" :class="{'flex': showSidebar}" class="min-h-screen bg-brand-black text-brand-white">
    <Sidebar v-if="showSidebar" />
    <main :class="{'flex-1': showSidebar}">
      <router-view />
    </main>
    <ToastContainer />
    <SessionExpiredModal v-if="authStore.sessionExpired" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import ToastContainer from './components/ToastContainer.vue'
import SessionExpiredModal from './components/SessionExpiredModal.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const showSidebar = computed(() => {
  return authStore.user && route.name !== 'Chat'
})
</script>

<style>
/* You can keep the global styles from the original App.vue if you want */
body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
</style>