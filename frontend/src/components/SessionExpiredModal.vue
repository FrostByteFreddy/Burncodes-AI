<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div class="bg-gray-800 rounded-lg shadow-xl p-8 max-w-md w-full text-center">
            <h2 class="text-2xl font-bold mb-4">Session Expired</h2>
            <p class="text-gray-300 mb-6">Your session has expired. Please log in again.</p>
            <button @click="onLogout" ref="logoutButton"
                class="px-6 py-2 text-white bg-blue-600 hover:bg-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400">
                Log Out
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const logoutButton = ref(null)

const onLogout = () => {
    authStore.logout()
}

onMounted(() => {
    // Focus the button when the modal is mounted
    logoutButton.value?.focus()
})
</script>
