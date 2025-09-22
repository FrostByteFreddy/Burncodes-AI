<template>
    <div class="bg-base-100 text-base-content" :class="isSidebarOpen ? 'overflow-hidden' : ''">
        <div class="flex">
            <Sidebar v-if="showSidebar" :is-open="isSidebarOpen" @close-sidebar="isSidebarOpen = false" />

            <div class="flex-1 flex flex-col h-100">
                <header v-if="showSidebar"
                    class="md:hidden flex items-center justify-between p-4 bg-base-100/80 backdrop-blur-lg border-b border-base-300 sticky top-0 z-10">
                    <button @click="isSidebarOpen = !isSidebarOpen" class="btn btn-square btn-ghost">
                        <font-awesome-icon :icon="['fas', 'bars']" class="h-6 w-6" />
                    </button>
                </header>

                <main class="flex-1">
                    <router-view />
                </main>
            </div>
        </div>

        <!-- Mobile sidebar overlay -->
        <div v-if="isSidebarOpen" @click="isSidebarOpen = false" class="fixed inset-0 bg-black/60 z-30 md:hidden"></div>

        <ToastContainer />
        <SessionExpiredModal v-if="authStore.sessionExpired" />
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import ToastContainer from './components/ToastContainer.vue'
import SessionExpiredModal from './components/SessionExpiredModal.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const isSidebarOpen = ref(false)

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