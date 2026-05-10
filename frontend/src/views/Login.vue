<template>
  <div class="min-h-screen flex">

    <!-- Left: Brand panel -->
    <div class="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden"
         style="background: linear-gradient(135deg, #0A1FAB 0%, #3B1FA8 40%, #FF2095 100%)">
      <div class="absolute inset-0 noise-overlay"></div>

      <div class="relative">
        <!-- Logo -->
        <img src="@/assets/logo.svg" alt="Logo" style="height:48px;width:auto;filter:brightness(0) invert(1);" />
      </div>

      <div class="relative">
        <p class="text-white/90 text-2xl font-light leading-relaxed mb-6">
          "The AI assistant that knows<br/>your business inside out."
        </p>
        <div class="flex items-center gap-3">
          <div class="w-8 h-px bg-white/40"></div>
          <span class="text-white/50 text-sm">Powered by Burncodes AI</span>
        </div>
      </div>
    </div>

    <!-- Right: Form panel -->
    <div class="flex-1 flex flex-col justify-center px-6 py-12 lg:px-16 bg-base-100">
      <!-- Mobile logo -->
      <div class="lg:hidden mb-10 flex justify-center">
        <img src="@/assets/logo.svg" alt="Logo" style="height:40px;width:auto;" />
      </div>

      <div class="w-full max-w-sm mx-auto lg:mx-0">
        <h1 class="text-3xl font-bold text-base-content mb-2">
          {{ $t("auth.login.title") }}
        </h1>
        <p class="text-base-content/50 text-sm mb-8">
          {{ $t("auth.login.noAccount") }}
          <router-link to="/signup" class="text-primary font-medium hover:underline">
            {{ $t("auth.login.signupLink") }}
          </router-link>
        </p>

        <form @submit.prevent="handleLogin" class="space-y-5">
          <div>
            <label for="email" class="block text-sm font-medium text-base-content mb-1.5">
              {{ $t("auth.login.email") }}
            </label>
            <input
              v-model="email"
              type="email"
              id="email"
              required
              autocomplete="email"
              class="w-full px-4 py-3 bg-base-200 border border-base-300 rounded-lg text-base-content placeholder:text-base-content/30 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              :placeholder="$t('auth.login.email')"
            />
          </div>

          <div>
            <div class="flex justify-between mb-1.5">
              <label for="password" class="text-sm font-medium text-base-content">
                {{ $t("auth.login.password") }}
              </label>
            </div>
            <input
              v-model="password"
              type="password"
              id="password"
              required
              autocomplete="current-password"
              class="w-full px-4 py-3 bg-base-200 border border-base-300 rounded-lg text-base-content placeholder:text-base-content/30 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              :placeholder="'••••••••'"
            />
          </div>

          <div v-if="errorMessage" class="flex items-center gap-2 text-error text-sm bg-error/10 px-4 py-3 rounded-lg">
            <font-awesome-icon :icon="['fas', 'circle-exclamation']" class="shrink-0" />
            {{ errorMessage }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 font-semibold text-white rounded-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            style="background: linear-gradient(135deg, #0A1FAB 0%, #FF2095 100%)"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <font-awesome-icon :icon="['fas', 'spinner']" class="animate-spin" />
              {{ $t("auth.login.submitting") }}
            </span>
            <span v-else>{{ $t("auth.login.submit") }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useAuthStore } from "../stores/auth";

const email = ref("");
const password = ref("");
const loading = ref(false);
const errorMessage = ref("");
const authStore = useAuthStore();

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = "";
  try {
    await authStore.login(email.value, password.value);
  } catch (error) {
    errorMessage.value = error.message || "An unknown error occurred.";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.noise-overlay {
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}
</style>
