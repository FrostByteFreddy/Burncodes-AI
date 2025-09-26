<template>
    <div :class="`rounded-md shadow-none sm:shadow-lg text-white px-6 py-4 ${toastClasses[type]}`">
        {{ message }}
    </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
    message: {
        type: String,
        required: true,
    },
    type: {
        type: String,
        default: 'success',
        validator: (value) => ['success', 'error'].includes(value),
    },
})

const toastClasses = {
    success: 'bg-green-700',
    error: 'bg-red-600',
}
</script>
