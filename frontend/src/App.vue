<template>
    <div class="bg-base-100 text-base-content">
        <!-- Default Layout: Navbar + content -->
        <div v-if="layout === 'default'" class="min-h-screen flex flex-col">
            <Navbar v-if="showNav" />
            <main class="flex-1 px-4 py-6 md:px-8 md:py-8 max-w-screen-xl mx-auto w-full">
                <router-view />
            </main>
        </div>

        <!-- Blank Layout (Login, Signup, Chat) -->
        <div v-else>
            <router-view />
        </div>

        <ToastContainer />
        <SessionExpiredModal v-if="authStore.sessionExpired" />
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'
import ToastContainer from './components/ToastContainer.vue'
import SessionExpiredModal from './components/SessionExpiredModal.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const route = useRoute()

const showNav = computed(() => !!authStore.user)

const layout = computed(() => {
    const layoutRoutes = ['Login', 'Signup', 'Chat']
    return layoutRoutes.includes(route.name) ? 'blank' : 'default'
})
</script>

<style>
body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
</style>