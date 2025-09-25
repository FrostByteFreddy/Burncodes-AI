<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div class="bg-gray-800 rounded-lg shadow-xl p-8 max-w-md w-full text-center">
            <h2 class="text-2xl font-bold mb-4 text-white">Session Expired</h2>
            <p class="text-gray-300 mb-6">Your session has expired. Please log in again.</p>
            <button @click="onLogout" ref="logoutButton"
                class="btn btn-primary">
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
