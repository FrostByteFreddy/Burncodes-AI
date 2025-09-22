<template>
    <div class="container mx-auto p-4 sm:p-6">
        <h1 class="text-3xl font-bold mb-6 flex items-center">
            <font-awesome-icon :icon="['fas', 'user-pen']" class="mr-3 text-primary" />
            My Profile
        </h1>
        <div class="max-w-2xl mx-auto bg-base-100 rounded-lg shadow-none sm:shadow-lg">
            <form v-if="authStore.user" @submit.prevent="handleUpdate" class="space-y-6">
                <div>
                    <label for="email" class="block text-sm font-medium text-base-content">Email</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                            <font-awesome-icon :icon="['fas', 'envelope']" class="w-5 h-5 text-gray-400" />
                        </span>
                        <input :value="authStore.user.email" type="email" id="email" disabled
                            class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg disabled:opacity-50" />
                    </div>
                </div>
                <div class="flex space-x-4">
                    <div class="w-1/2">
                        <label for="firstName" class="block text-sm font-medium text-base-content">First Name</label>
                        <div class="relative">
                            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                                <font-awesome-icon :icon="['fas', 'user']" class="w-5 h-5 text-gray-400" />
                            </span>
                            <input v-model="formData.first_name" type="text" id="firstName"
                                class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                        </div>
                    </div>
                    <div class="w-1/2">
                        <label for="lastName" class="block text-sm font-medium text-base-content">Last Name</label>
                        <div class="relative">
                            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                                <font-awesome-icon :icon="['fas', 'user']" class="w-5 h-5 text-gray-400" />
                            </span>
                            <input v-model="formData.last_name" type="text" id="lastName"
                                class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                        </div>
                    </div>
                </div>
                <div>
                    <label for="phone_number" class="block text-sm font-medium text-base-content">Phone Number</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                            <font-awesome-icon :icon="['fas', 'phone']" class="w-5 h-5 text-gray-400" />
                        </span>
                        <input v-model="formData.phone_number" type="tel" id="phone_number"
                            class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                    </div>
                </div>
                <div class="flex justify-end">
                    <button type="submit" :disabled="loading" class="btn btn-primary">
                        <span v-if="loading" class="flex items-center justify-center">
                            <font-awesome-icon :icon="['fas', 'spinner']" class="w-5 h-5 mr-3 animate-spin" />
                            Saving...
                        </span>
                        <span v-else class="flex items-center">
                            <font-awesome-icon :icon="['fas', 'save']" class="mr-2" />
                            Save Changes
                        </span>
                    </button>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'

const authStore = useAuthStore()
const { addToast } = useToast()
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
        addToast('Profile updated successfully!', 'success')
    } catch (error) {
        console.error('Failed to update profile:', error)
        addToast('Failed to update profile.', 'error')
    } finally {
        loading.value = false
    }
}
</script>
