<template>
  <div class="flex items-center justify-center min-h-screen bg-brand-black">
    <div class="w-full max-w-md p-8 space-y-8 bg-gray-800 rounded-2xl shadow-lg">
      <h1 class="text-4xl font-extrabold text-center text-brand-white">
        Login
      </h1>
      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label for="email" class="text-sm font-medium text-gray-300">Email</label>
          <input v-model="email" type="email" id="email" required
            class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-white" />
        </div>
        <div>
          <label for="password" class="text-sm font-medium text-gray-300">Password</label>
          <input v-model="password" type="password" id="password" required
            class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-white" />
        </div>
        <div v-if="errorMessage" class="text-red-400 text-sm">
          {{ errorMessage }}
        </div>
        <button type="submit" :disabled="loading"
          class="w-full py-3 font-semibold text-white bg-black border border-white rounded-lg hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white disabled:opacity-50">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>
       <p class="text-sm text-center text-gray-400">
        Don't have an account?
        <router-link to="/signup" class="font-medium text-white hover:underline">Sign up</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const authStore = useAuthStore()

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    await authStore.login(email.value, password.value)
    // The store handles redirection
  } catch (error) {
    errorMessage.value = error.message || 'An unknown error occurred.'
  } finally {
    loading.value = false
  }
}
</script>
