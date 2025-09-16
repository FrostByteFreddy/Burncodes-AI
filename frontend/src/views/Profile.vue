<template>
  <div class="container mx-auto p-6">
    <h1 class="text-3xl font-bold mb-6">My Profile</h1>
    <div class="max-w-2xl mx-auto bg-gray-800 p-8 rounded-lg shadow-lg">
      <form v-if="authStore.user" @submit.prevent="handleUpdate" class="space-y-6">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-300">Email</label>
          <input :value="authStore.user.email" type="email" id="email" disabled
            class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg disabled:opacity-50" />
        </div>
        <div class="flex space-x-4">
          <div class="w-1/2">
            <label for="firstName" class="block text-sm font-medium text-gray-300">First Name</label>
            <input v-model="formData.first_name" type="text" id="firstName"
              class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
          </div>
          <div class="w-1/2">
            <label for="lastName" class="block text-sm font-medium text-gray-300">Last Name</label>
            <input v-model="formData.last_name" type="text" id="lastName"
              class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
          </div>
        </div>
        <div>
          <label for="phone_number" class="block text-sm font-medium text-gray-300">Phone Number</label>
          <input v-model="formData.phone_number" type="tel" id="phone_number"
            class="w-full p-3 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
        </div>
        <div class="flex justify-end">
          <button type="submit" :disabled="loading"
            class="bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
            {{ loading ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const formData = ref({
  first_name: '',
  last_name: '',
  phone_number: ''
})

const setFormData = () => {
    if (authStore.user && authStore.user.user_metadata) {
        formData.value = {
            first_name: authStore.user.user_metadata.first_name,
            last_name: authStore.user.user_metadata.last_name,
            phone_number: authStore.user.user_metadata.phone_number,
        }
    }
}

onMounted(async () => {
    // Ensure user and profile data is loaded
    if (!authStore.user) {
        await authStore.fetchUser();
    }
    setFormData();
})

watch(() => authStore.user, setFormData, { deep: true })

const handleUpdate = async () => {
  loading.value = true
  try {
    await authStore.updateProfile(formData.value)
    // Optionally show success message
    alert('Profile updated successfully!')
  } catch (error) {
    console.error('Failed to update profile:', error)
    alert('Failed to update profile.')
  } finally {
    loading.value = false
  }
}
</script>
