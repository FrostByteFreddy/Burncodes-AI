<template>
  <div :class="`p-4 rounded-md shadow-lg text-white ${toastClasses[type]}`">
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
  success: 'bg-green-500',
  error: 'bg-red-500',
}
</script>
