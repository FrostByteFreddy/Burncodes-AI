<template>
  <div class="min-h-screen flex">

    <!-- Left: Brand panel -->
    <div class="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden"
         style="background: linear-gradient(135deg, #0A1FAB 0%, #3B1FA8 40%, #FF2095 100%)">
      <div class="absolute inset-0 opacity-[0.03]"
           style="background-image: url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")">
      </div>

      <div class="relative">
        <svg width="120" height="48" viewBox="0 0 476 294" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M37.5312 140H1.69141C1.17057 140 0.910156 139.674 0.910156 139.023L1.30078 1.62109C1.30078 1.10026 1.5612 0.839844 2.08203 0.839844H40.5586C48.0456 0.839844 54.849 2.66276 60.9688 6.30859C66.9583 9.95443 71.6784 14.8047 75.1289 20.8594C78.5794 26.849 80.3047 33.3594 80.3047 40.3906C80.3047 46.1198 79.0026 51.4583 76.3984 56.4062C73.7943 61.3542 70.7018 65.3581 67.1211 68.418C70.9622 72.2591 73.957 76.7188 76.1055 81.7969C78.2539 86.875 79.3281 92.2135 79.3281 97.8125C79.3281 105.56 77.4727 112.624 73.7617 119.004C69.9857 125.384 64.9401 130.495 58.625 134.336C52.3099 138.112 45.2786 140 37.5312 140ZM40.5586 24.5703H25.3242V56.0156H40.5586C45.181 56.0156 48.9245 54.388 51.7891 51.1328C54.6536 47.8125 56.0859 44.2318 56.0859 40.3906C56.0859 36.1589 54.556 32.4805 51.4961 29.3555C48.4362 26.1654 44.7904 24.5703 40.5586 24.5703ZM37.5312 80.2344H25.3242L25.1289 115.586H37.5312C42.349 115.586 46.4831 113.828 49.9336 110.312C53.3841 106.797 55.1094 102.63 55.1094 97.8125C55.1094 92.9948 53.3841 88.8607 49.9336 85.4102C46.4831 81.9596 42.349 80.2344 37.5312 80.2344ZM130.5 141.953C123.469 141.953 116.958 140.13 110.969 136.484C104.979 132.839 100.194 127.956 96.6133 121.836C93.0977 115.651 91.3398 108.913 91.3398 101.621L91.7305 1.62109C91.7305 1.10026 91.9909 0.839844 92.5117 0.839844H114.973C115.493 0.839844 115.754 1.10026 115.754 1.62109V101.621C115.754 106.113 117.186 109.954 120.051 113.145C122.915 116.27 126.398 117.832 130.5 117.832C134.797 117.832 138.378 116.27 141.242 113.145C144.107 109.954 145.539 106.113 145.539 101.621V1.62109C145.539 1.10026 145.799 0.839844 146.32 0.839844H168.781C169.302 0.839844 169.562 1.10026 169.562 1.62109L169.953 101.621C169.953 108.978 168.195 115.749 164.68 121.934C161.099 128.053 156.346 132.936 150.422 136.582C144.497 140.163 137.857 141.953 130.5 141.953ZM209.113 140H186.457C185.936 140 185.676 139.674 185.676 139.023L186.066 1.62109C186.066 1.10026 186.327 0.839844 186.848 0.839844H227.277C234.504 0.839844 241.145 2.59766 247.199 6.11328C253.254 9.62891 258.072 14.349 261.652 20.2734C265.298 26.1979 267.121 32.9036 267.121 40.3906C267.121 45.2734 266.372 49.7005 264.875 53.6719C263.378 57.6432 261.62 60.9961 259.602 63.7305C257.648 66.4648 255.858 68.4831 254.23 69.7852C261.457 77.793 265.07 87.2005 265.07 98.0078L265.266 139.023C265.266 139.674 264.94 140 264.289 140H241.633C241.112 140 240.852 139.805 240.852 139.414V98.0078C240.852 93.1901 239.159 89.0234 235.773 85.5078C232.388 81.9922 228.221 80.2344 223.273 80.2344H210.09L209.895 139.023C209.895 139.674 209.634 140 209.113 140ZM227.277 24.7656H210.09V56.2109H227.277C231.379 56.2109 235.025 54.681 238.215 51.6211C241.47 48.5612 243.098 44.8177 243.098 40.3906C243.098 36.1589 241.535 32.513 238.41 29.4531C235.285 26.3281 231.574 24.7656 227.277 24.7656ZM303.938 140H283.918C282.876 140 282.355 139.544 282.355 138.633L282.16 2.40234C282.16 1.36068 282.681 0.839844 283.723 0.839844H301.789L335.578 79.6484L334.602 2.40234C334.602 1.36068 335.188 0.839844 336.359 0.839844H356.184C356.965 0.839844 357.355 1.36068 357.355 2.40234L357.551 138.828C357.551 139.609 357.225 140 356.574 140H338.996L304.328 66.3672L305.793 138.438C305.793 139.479 305.174 140 303.938 140Z" fill="white"/>
        </svg>
      </div>

      <div class="relative">
        <p class="text-white/90 text-2xl font-light leading-relaxed mb-6">
          "Set up your AI chatbot<br/>in minutes, not months."
        </p>
        <div class="flex items-center gap-3">
          <div class="w-8 h-px bg-white/40"></div>
          <span class="text-white/50 text-sm">Powered by SwiftAnswer</span>
        </div>
      </div>
    </div>

    <!-- Right: Form panel -->
    <div class="flex-1 flex flex-col justify-center px-6 py-12 lg:px-16 bg-base-100 overflow-y-auto">
      <!-- Mobile logo -->
      <div class="lg:hidden mb-10 flex justify-center">
        <svg width="100" height="40" viewBox="0 0 476 294" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M37.5312 140H1.69141C1.17057 140 0.910156 139.674 0.910156 139.023L1.30078 1.62109C1.30078 1.10026 1.5612 0.839844 2.08203 0.839844H40.5586C48.0456 0.839844 54.849 2.66276 60.9688 6.30859C66.9583 9.95443 71.6784 14.8047 75.1289 20.8594C78.5794 26.849 80.3047 33.3594 80.3047 40.3906C80.3047 46.1198 79.0026 51.4583 76.3984 56.4062C73.7943 61.3542 70.7018 65.3581 67.1211 68.418C70.9622 72.2591 73.957 76.7188 76.1055 81.7969C78.2539 86.875 79.3281 92.2135 79.3281 97.8125C79.3281 105.56 77.4727 112.624 73.7617 119.004C69.9857 125.384 64.9401 130.495 58.625 134.336C52.3099 138.112 45.2786 140 37.5312 140ZM40.5586 24.5703H25.3242V56.0156H40.5586C45.181 56.0156 48.9245 54.388 51.7891 51.1328C54.6536 47.8125 56.0859 44.2318 56.0859 40.3906C56.0859 36.1589 54.556 32.4805 51.4961 29.3555C48.4362 26.1654 44.7904 24.5703 40.5586 24.5703ZM37.5312 80.2344H25.3242L25.1289 115.586H37.5312C42.349 115.586 46.4831 113.828 49.9336 110.312C53.3841 106.797 55.1094 102.63 55.1094 97.8125C55.1094 92.9948 53.3841 88.8607 49.9336 85.4102C46.4831 81.9596 42.349 80.2344 37.5312 80.2344ZM130.5 141.953C123.469 141.953 116.958 140.13 110.969 136.484C104.979 132.839 100.194 127.956 96.6133 121.836C93.0977 115.651 91.3398 108.913 91.3398 101.621L91.7305 1.62109C91.7305 1.10026 91.9909 0.839844 92.5117 0.839844H114.973C115.493 0.839844 115.754 1.10026 115.754 1.62109V101.621C115.754 106.113 117.186 109.954 120.051 113.145C122.915 116.27 126.398 117.832 130.5 117.832C134.797 117.832 138.378 116.27 141.242 113.145C144.107 109.954 145.539 106.113 145.539 101.621V1.62109C145.539 1.10026 145.799 0.839844 146.32 0.839844H168.781C169.302 0.839844 169.562 1.10026 169.562 1.62109L169.953 101.621C169.953 108.978 168.195 115.749 164.68 121.934C161.099 128.053 156.346 132.936 150.422 136.582C144.497 140.163 137.857 141.953 130.5 141.953ZM209.113 140H186.457C185.936 140 185.676 139.674 185.676 139.023L186.066 1.62109C186.066 1.10026 186.327 0.839844 186.848 0.839844H227.277C234.504 0.839844 241.145 2.59766 247.199 6.11328C253.254 9.62891 258.072 14.349 261.652 20.2734C265.298 26.1979 267.121 32.9036 267.121 40.3906C267.121 45.2734 266.372 49.7005 264.875 53.6719C263.378 57.6432 261.62 60.9961 259.602 63.7305C257.648 66.4648 255.858 68.4831 254.23 69.7852C261.457 77.793 265.07 87.2005 265.07 98.0078L265.266 139.023C265.266 139.674 264.94 140 264.289 140H241.633C241.112 140 240.852 139.805 240.852 139.414V98.0078C240.852 93.1901 239.159 89.0234 235.773 85.5078C232.388 81.9922 228.221 80.2344 223.273 80.2344H210.09L209.895 139.023C209.895 139.674 209.634 140 209.113 140ZM227.277 24.7656H210.09V56.2109H227.277C231.379 56.2109 235.025 54.681 238.215 51.6211C241.47 48.5612 243.098 44.8177 243.098 40.3906C243.098 36.1589 241.535 32.513 238.41 29.4531C235.285 26.3281 231.574 24.7656 227.277 24.7656ZM303.938 140H283.918C282.876 140 282.355 139.544 282.355 138.633L282.16 2.40234C282.16 1.36068 282.681 0.839844 283.723 0.839844H301.789L335.578 79.6484L334.602 2.40234C334.602 1.36068 335.188 0.839844 336.359 0.839844H356.184C356.965 0.839844 357.355 1.36068 357.355 2.40234L357.551 138.828C357.551 139.609 357.225 140 356.574 140H338.996L304.328 66.3672L305.793 138.438C305.793 139.479 305.174 140 303.938 140Z"
                fill="url(#mobile_gradient_signup)"/>
          <defs>
            <linearGradient id="mobile_gradient_signup" x1="476" y1="0" x2="0" y2="294" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stop-color="#50D3FC"/>
              <stop offset="50%" stop-color="#0A1FAB"/>
              <stop offset="100%" stop-color="#FF2095"/>
            </linearGradient>
          </defs>
        </svg>
      </div>

      <div class="w-full max-w-sm mx-auto lg:mx-0">
        <h1 class="text-3xl font-bold text-base-content mb-2">
          {{ $t("auth.signup.title") }}
        </h1>
        <p class="text-base-content/50 text-sm mb-8">
          {{ $t("auth.signup.alreadyHaveAccount") }}
          <router-link to="/login" class="text-primary font-medium hover:underline">
            {{ $t("auth.signup.loginLink") }}
          </router-link>
        </p>

        <form @submit.prevent="handleSignup" class="space-y-4">
          <div class="flex gap-4">
            <div class="flex-1">
              <label for="firstName" class="block text-sm font-medium text-base-content mb-1.5">
                {{ $t("auth.signup.firstName") }}
              </label>
              <input
                v-model="firstName"
                type="text"
                id="firstName"
                required
                autocomplete="given-name"
                class="w-full px-4 py-3 bg-base-200 border border-base-300 rounded-lg text-base-content focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              />
            </div>
            <div class="flex-1">
              <label for="lastName" class="block text-sm font-medium text-base-content mb-1.5">
                {{ $t("auth.signup.lastName") }}
              </label>
              <input
                v-model="lastName"
                type="text"
                id="lastName"
                required
                autocomplete="family-name"
                class="w-full px-4 py-3 bg-base-200 border border-base-300 rounded-lg text-base-content focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-base-content mb-1.5">
              {{ $t("auth.signup.email") }}
            </label>
            <input
              v-model="email"
              type="email"
              id="email"
              required
              autocomplete="email"
              class="w-full px-4 py-3 bg-base-200 border border-base-300 rounded-lg text-base-content focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              :placeholder="$t('auth.signup.email')"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-base-content mb-1.5">
              {{ $t("auth.signup.password") }}
            </label>
            <input
              v-model="password"
              type="password"
              id="password"
              required
              autocomplete="new-password"
              class="w-full px-4 py-3 bg-base-200 border border-base-300 rounded-lg text-base-content focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label for="language" class="block text-sm font-medium text-base-content mb-1.5">
              {{ $t("auth.signup.language") }}
            </label>
            <div class="relative">
              <select
                v-model="language"
                id="language"
                required
                class="w-full px-4 py-3 bg-base-200 border border-base-300 rounded-lg text-base-content focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent appearance-none transition-all"
              >
                <option value="en">English</option>
                <option value="de">Deutsch</option>
                <option value="fr">Français</option>
              </select>
              <span class="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                <font-awesome-icon :icon="['fas', 'chevron-down']" class="w-4 h-4 text-base-content/40" />
              </span>
            </div>
          </div>

          <div
            v-if="message"
            class="flex items-center gap-2 text-sm px-4 py-3 rounded-lg"
            :class="isError ? 'text-error bg-error/10' : 'text-success bg-success/10'"
          >
            <font-awesome-icon :icon="['fas', isError ? 'circle-exclamation' : 'circle-check']" class="shrink-0" />
            {{ message }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 font-semibold text-white rounded-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            style="background: linear-gradient(135deg, #0A1FAB 0%, #FF2095 100%)"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <font-awesome-icon :icon="['fas', 'spinner']" class="animate-spin" />
              {{ $t("auth.signup.submitting") }}
            </span>
            <span v-else>{{ $t("auth.signup.submit") }}</span>
          </button>
        </form>
      </div>
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
    await authStore.signUp(email.value, password.value, firstName.value, lastName.value, language.value);
    message.value = t("auth.signup.successMessage");
  } catch (error) {
    message.value = error.message || "An unknown error occurred.";
    isError.value = true;
  } finally {
    loading.value = false;
  }
};
</script>
