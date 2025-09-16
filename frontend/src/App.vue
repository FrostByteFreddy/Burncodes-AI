<template>
  <div id="app-layout" class="min-h-screen bg-gray-900 text-white">
    <header v-if="authStore.user" class="bg-gray-800 shadow-md">
      <nav class="container mx-auto px-6 py-3 flex justify-between items-center">
        <router-link to="/dashboard" class="text-2xl font-bold bg-gradient-to-r from-orange-500 to-red-600 bg-clip-text text-transparent">
          SwiftAnswer
        </router-link>
        <div class="flex items-center space-x-4">
          <router-link to="/dashboard" class="text-gray-300 hover:text-white">Dashboard</router-link>
          <router-link to="/profile" class="text-gray-300 hover:text-white">Profile</router-link>
          <button @click="handleLogout" class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg">
            Logout
          </button>
        </div>
      </nav>
    </header>

    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = async () => {
  await authStore.logout()
}
</script>

<style>
/* You can keep the global styles from the original App.vue if you want */
body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
</style>