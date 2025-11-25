<template>
  <div class="flex items-center justify-center min-h-screen bg-base-200">
    <div class="w-full max-w-md p-8 space-y-8 card-login">
      <h1 class="text-4xl font-extrabold text-center text-base-content">
        {{ $t("auth.signup.title") }}
      </h1>
      <form @submit.prevent="handleSignup" class="space-y-6">
        <div class="flex space-x-4">
          <div class="w-1/2">
            <label
              for="firstName"
              class="text-sm font-medium text-base-content"
              >{{ $t("auth.signup.firstName") }}</label
            >
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                <font-awesome-icon
                  :icon="['fas', 'user']"
                  class="w-5 h-5 text-gray-400"
                />
              </span>
              <input
                v-model="firstName"
                type="text"
                id="firstName"
                required
                class="w-full p-3 pl-10 mt-1 text-base-content bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div class="w-1/2">
            <label
              for="lastName"
              class="text-sm font-medium text-base-content"
              >{{ $t("auth.signup.lastName") }}</label
            >
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                <font-awesome-icon
                  :icon="['fas', 'user']"
                  class="w-5 h-5 text-gray-400"
                />
              </span>
              <input
                v-model="lastName"
                type="text"
                id="lastName"
                required
                class="w-full p-3 pl-10 mt-1 text-base-content bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        </div>
        <div>
          <label for="email" class="text-sm font-medium text-base-content">{{
            $t("auth.signup.email")
          }}</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
              <font-awesome-icon
                :icon="['fas', 'envelope']"
                class="w-5 h-5 text-gray-400"
              />
            </span>
            <input
              v-model="email"
              type="email"
              id="email"
              required
              class="w-full p-3 pl-10 mt-1 text-base-content bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
        <div>
          <label for="password" class="text-sm font-medium text-base-content">{{
            $t("auth.signup.password")
          }}</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
              <font-awesome-icon
                :icon="['fas', 'lock']"
                class="w-5 h-5 text-gray-400"
              />
            </span>
            <input
              v-model="password"
              type="password"
              id="password"
              required
              class="w-full p-3 pl-10 mt-1 text-base-content bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
        <div>
          <label for="language" class="text-sm font-medium text-base-content">{{
            $t("auth.signup.language")
          }}</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3">
              <font-awesome-icon
                :icon="['fas', 'globe']"
                class="w-5 h-5 text-gray-400"
              />
            </span>
            <select
              v-model="language"
              id="language"
              required
              class="w-full p-3 pl-10 mt-1 text-base-content bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary appearance-none"
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
        <div
          v-if="message"
          class="text-sm"
          :class="isError ? 'text-error' : 'text-success'"
        >
          {{ message }}
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 font-semibold text-primary-content bg-primary rounded-lg hover:bg-primary-focus focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-base-100 focus:ring-primary disabled:opacity-50"
        >
          <span v-if="loading" class="flex items-center justify-center">
            <font-awesome-icon
              :icon="['fas', 'spinner']"
              class="w-5 h-5 mr-3 animate-spin"
            />
            {{ $t("auth.signup.submitting") }}
          </span>
          <span v-else>{{ $t("auth.signup.submit") }}</span>
        </button>
      </form>
      <p class="text-sm text-center text-base-content opacity-75">
        {{ $t("auth.signup.alreadyHaveAccount") }}
        <router-link
          to="/login"
          class="font-medium text-primary hover:underline"
          >{{ $t("auth.signup.loginLink") }}</router-link
        >
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useAuthStore } from "../stores/auth";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const email = ref("");
const password = ref("");
const firstName = ref("");
const lastName = ref("");
const language = ref("en");
const loading = ref(false);
const message = ref("");
const isError = ref(false);
const authStore = useAuthStore();

const handleSignup = async () => {
  loading.value = true;
  message.value = "";
  isError.value = false;
  try {
    await authStore.signUp(
      email.value,
      password.value,
      firstName.value,
      lastName.value,
      language.value
    );
    message.value = t("auth.signup.successMessage");
  } catch (error) {
    message.value = error.message || "An unknown error occurred.";
    isError.value = true;
  } finally {
    loading.value = false;
  }
};
</script>
