<template>
  <div class="container mx-auto p-4 sm:p-6">
    <h1 class="text-3xl font-bold mb-6 flex items-center">
      <font-awesome-icon
        :icon="['fas', 'user-pen']"
        class="mr-3 text-primary"
      />
      {{ $t("profile.title") }}
    </h1>
    <div class="max-w-2xl mx-auto card">
      <form
        v-if="authStore.user"
        @submit.prevent="handleUpdate"
        class="space-y-6"
      >
        <div>
          <label
            for="email"
            class="block text-sm font-medium text-base-content"
            >{{ $t("profile.email") }}</label
          >
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
              <font-awesome-icon
                :icon="['fas', 'envelope']"
                class="w-5 h-5 text-gray-400"
              />
            </span>
            <input
              :value="authStore.user.email"
              type="email"
              id="email"
              disabled
              class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg disabled:opacity-50"
            />
          </div>
        </div>
        <div class="flex space-x-4">
          <div class="w-1/2">
            <label
              for="firstName"
              class="block text-sm font-medium text-base-content"
              >{{ $t("profile.first_name") }}</label
            >
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                <font-awesome-icon
                  :icon="['fas', 'user']"
                  class="w-5 h-5 text-gray-400"
                />
              </span>
              <input
                v-model="formData.first_name"
                type="text"
                id="firstName"
                class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div class="w-1/2">
            <label
              for="lastName"
              class="block text-sm font-medium text-base-content"
              >{{ $t("profile.last_name") }}</label
            >
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                <font-awesome-icon
                  :icon="['fas', 'user']"
                  class="w-5 h-5 text-gray-400"
                />
              </span>
              <input
                v-model="formData.last_name"
                type="text"
                id="lastName"
                class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        </div>
        <div>
          <label
            for="phone_number"
            class="block text-sm font-medium text-base-content"
            >{{ $t("profile.phone_number") }}</label
          >
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
              <font-awesome-icon
                :icon="['fas', 'phone']"
                class="w-5 h-5 text-gray-400"
              />
            </span>
            <input
              v-model="formData.phone_number"
              type="tel"
              id="phone_number"
              class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
        <div>
          <label
            for="language"
            class="block text-sm font-medium text-base-content"
            >{{ $t("profile.language") }}</label
          >
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
              <font-awesome-icon
                :icon="['fas', 'globe']"
                class="w-5 h-5 text-gray-400"
              />
            </span>
            <select
              v-model="formData.language"
              id="language"
              class="w-full p-3 pl-10 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary appearance-none"
            >
              <option value="en">English</option>
              <option value="de">Deutsch</option>
              <option value="fr">Français</option>
            </select>
            <span
              class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none"
            >
              <font-awesome-icon
                :icon="['fas', 'chevron-down']"
                class="w-4 h-4 text-gray-400"
              />
            </span>
          </div>
        </div>
        <div class="flex justify-end">
          <button type="submit" :disabled="loading" class="btn btn-primary">
            <span v-if="loading" class="flex items-center justify-center">
              <font-awesome-icon
                :icon="['fas', 'spinner']"
                class="w-5 h-5 mr-3 animate-spin"
              />
              {{ $t("profile.saving") }}...
            </span>
            <span v-else class="flex items-center">
              <font-awesome-icon :icon="['fas', 'save']" class="mr-2" />
              {{ $t("profile.save_changes") }}
            </span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import { useToast } from "../composables/useToast";
import { useI18n } from "vue-i18n";

const authStore = useAuthStore();
const { addToast } = useToast();
const { t, locale } = useI18n();
const loading = ref(false);
const formData = ref({
  first_name: "",
  last_name: "",
  phone_number: "",
  language: "en",
});

const setFormData = () => {
  if (authStore.user && authStore.user.user_metadata) {
    formData.value = {
      first_name: authStore.user.user_metadata.first_name,
      last_name: authStore.user.user_metadata.last_name,
      phone_number: authStore.user.user_metadata.phone_number,
      language: authStore.user.user_metadata.language || "en",
    };
  }
};

onMounted(async () => {
  // Ensure user and profile data is loaded
  if (!authStore.user) {
    await authStore.fetchUser();
  }
  setFormData();
});

watch(() => authStore.user, setFormData, { deep: true });

const handleUpdate = async () => {
  loading.value = true;
  try {
    await authStore.updateProfile(formData.value);

    // Update local language immediately
    if (formData.value.language) {
      locale.value = formData.value.language;
    }

    addToast(t("profile.success"), "success");
  } catch (error) {
    console.error("Failed to update profile:", error);
    addToast(t("profile.error"), "error");
  } finally {
    loading.value = false;
  }
};
</script>
