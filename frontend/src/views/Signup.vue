<template>
  <div class="flex items-center justify-center min-h-screen bg-brand-black">
    <div class="w-full max-w-md p-8 space-y-8 bg-gray-800 rounded-2xl shadow-lg">
      <h1 class="text-4xl font-extrabold text-center text-brand-white">
        Create Account
      </h1>
      <form @submit.prevent="handleSignup" class="space-y-6">
        <div class="flex space-x-4">
          <div class="w-1/2">
            <label for="firstName" class="text-sm font-medium text-gray-300">First Name</label>
            <input v-model="firstName" type="text" id="firstName" required
              class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-white" />
          </div>
          <div class="w-1/2">
            <label for="lastName" class="text-sm font-medium text-gray-300">Last Name</label>
            <input v-model="lastName" type="text" id="lastName" required
              class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-white" />
          </div>
        </div>
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
        <div v-if="message" class="text-sm" :class="isError ? 'text-red-400' : 'text-green-400'">
          {{ message }}
        </div>
        <button type="submit" :disabled="loading"
          class="w-full py-3 font-semibold text-white bg-black border border-white rounded-lg hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white disabled:opacity-50">
          {{ loading ? 'Creating...' : 'Sign Up' }}
        </button>
      </form>
      <p class="text-sm text-center text-gray-400">
        Already have an account?
        <router-link to="/login" class="font-medium text-white hover:underline">Log in</router-link>
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
