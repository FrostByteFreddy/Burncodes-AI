<template>
    <div class="flex items-center justify-center min-h-screen bg-base-200">
        <div class="w-full max-w-md p-8 space-y-8 bg-base-100 rounded-2xl shadow-lg">
            <h1 class="text-4xl font-extrabold text-center text-base-content">
                Login
            </h1>
            <form @submit.prevent="handleLogin" class="space-y-6">
                <div>
                    <label for="email" class="text-sm font-medium text-base-content">Email</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                            <font-awesome-icon :icon="['fas', 'envelope']" class="w-5 h-5 text-gray-400" />
                        </span>
                        <input v-model="email" type="email" id="email" required
                            class="w-full p-3 pl-10 mt-1 text-base-content bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                    </div>
                </div>
                <div>
                    <label for="password" class="text-sm font-medium text-base-content">Password</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                            <font-awesome-icon :icon="['fas', 'lock']" class="w-5 h-5 text-gray-400" />
                        </span>
                        <input v-model="password" type="password" id="password" required
                            class="w-full p-3 pl-10 mt-1 text-base-content bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                    </div>
                </div>
                <div v-if="errorMessage" class="text-error text-sm">
                    {{ errorMessage }}
                </div>
                <button type="submit" :disabled="loading"
                    class="w-full py-3 font-semibold text-primary-content bg-primary rounded-lg hover:bg-primary-focus focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-base-100 focus:ring-primary disabled:opacity-50">
                    <span v-if="loading" class="flex items-center justify-center">
                        <font-awesome-icon :icon="['fas', 'spinner']" class="w-5 h-5 mr-3 animate-spin" />
                        Logging in...
                    </span>
                    <span v-else>Login</span>
                </button>
            </form>
            <p class="text-sm text-center text-base-content opacity-75">
                Don't have an account?
                <router-link to="/signup" class="font-medium text-primary hover:underline">Sign up</router-link>
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
