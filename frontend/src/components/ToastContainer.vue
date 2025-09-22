<template>
    <div class="fixed bottom-4 right-4 z-50 space-y-4">
        <Toast v-for="toast in toasts" :key="toast.id" :message="toast.message" :type="toast.type" />
    </div>
</template>

<script setup>
import Toast from './Toast.vue'
import { useToast } from '../composables/useToast'

const { toasts } = useToast()
</script>
