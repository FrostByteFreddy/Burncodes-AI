<template>
  <div id="app-layout" class="flex min-h-screen bg-brand-black text-brand-white">
    <Sidebar v-if="authStore.user" />
    <main class="flex-1">
      <router-view />
    </main>
    <ToastContainer />
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import ToastContainer from './components/ToastContainer.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
</script>

<style>
/* You can keep the global styles from the original App.vue if you want */
body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
</style>