<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-900">
    <div class="w-full max-w-md p-8 space-y-8 bg-gray-800 rounded-2xl shadow-lg">
      <h1 class="text-4xl font-extrabold text-center text-white">
        <span class="bg-gradient-to-r from-orange-500 to-red-600 bg-clip-text text-transparent">Create Account</span>
      </h1>
      <form @submit.prevent="handleSignup" class="space-y-6">
        <div class="flex space-x-4">
          <div class="w-1/2">
            <label for="firstName" class="text-sm font-medium text-gray-300">First Name</label>
            <input v-model="firstName" type="text" id="firstName" required
              class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
          </div>
          <div class="w-1/2">
            <label for="lastName" class="text-sm font-medium text-gray-300">Last Name</label>
            <input v-model="lastName" type="text" id="lastName" required
              class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
          </div>
        </div>
        <div>
          <label for="email" class="text-sm font-medium text-gray-300">Email</label>
          <input v-model="email" type="email" id="email" required
            class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
        </div>
        <div>
          <label for="password" class="text-sm font-medium text-gray-300">Password</label>
          <input v-model="password" type="password" id="password" required
            class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
        </div>
        <div v-if="message" class="text-sm" :class="isError ? 'text-red-400' : 'text-green-400'">
          {{ message }}
        </div>
        <button type="submit" :disabled="loading"
          class="w-full py-3 font-semibold text-white bg-gradient-to-r from-orange-500 to-red-600 rounded-lg hover:from-orange-600 hover:to-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-orange-500 disabled:opacity-50">
          {{ loading ? 'Creating...' : 'Sign Up' }}
        </button>
      </form>
      <p class="text-sm text-center text-gray-400">
        Already have an account?
        <router-link to="/login" class="font-medium text-orange-400 hover:underline">Log in</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')
const firstName = ref('')
const lastName = ref('')
const loading = ref(false)
const message = ref('')
const isError = ref(false)
const authStore = useAuthStore()

const handleSignup = async () => {
  loading.value = true
  message.value = ''
  isError.value = false
  try {
    await authStore.signUp(email.value, password.value, firstName.value, lastName.value)
    message.value = 'Signup successful! Please check your email to confirm your account.'
  } catch (error) {
    message.value = error.message || 'An unknown error occurred.'
    isError.value = true
  } finally {
    loading.value = false
  }
}
</script>
