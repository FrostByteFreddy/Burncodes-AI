<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-gray-800 rounded-lg shadow-xl p-8 max-w-md w-full">
      <h2 class="text-2xl font-bold mb-4">{{ title }}</h2>
      <p class="text-gray-300 mb-6">{{ message }}</p>

      <div v-if="confirmationText">
        <label class="block text-sm font-medium text-gray-400 mb-2">
          To confirm, please type "<span class="font-bold">{{ confirmationText }}</span>" below:
        </label>
        <input
          v-model="userInput"
          type="text"
          class="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div class="flex justify-end mt-8 space-x-4">
        <button @click="onCancel" class="px-6 py-2 text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-md">
          Cancel
        </button>
        <button
          @click="onConfirm"
          :disabled="isConfirmDisabled"
          class="px-6 py-2 text-white bg-red-600 hover:bg-red-500 rounded-md disabled:bg-red-800 disabled:cursor-not-allowed"
        >
          {{ confirmButtonText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue'

const props = defineProps({
  show: Boolean,
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  confirmationText: {
    type: String,
    default: '',
  },
  confirmButtonText: {
    type: String,
    default: 'Confirm',
  },
})

const emit = defineEmits(['confirm', 'cancel'])

const userInput = ref('')

const isConfirmDisabled = computed(() => {
  return props.confirmationText && userInput.value !== props.confirmationText
})

const onConfirm = () => {
  if (!isConfirmDisabled.value) {
    emit('confirm')
  }
}

const onCancel = () => {
  emit('cancel')
}
</script>
