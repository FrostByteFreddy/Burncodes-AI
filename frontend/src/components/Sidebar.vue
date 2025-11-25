<template>
  <aside
    class="fixed inset-y-0 left-0 z-40 w-3/4 sm:w-64 bg-neutral text-neutral-content transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full'"
  >
    <div class="flex flex-col h-screen px-4 py-8">
      <div class="relative sm:mt-6">
        <!-- Logo -->
        <div class="sidebar-logo">
          <svg
            width="200"
            height="100"
            viewBox="0 0 475 294"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M36.621 139.16H0.781254C0.260414 139.16 0 138.834 0 138.183L0.390624 0.781246C0.390624 0.260416 0.651044 0 1.17187 0H39.6484C47.1354 0 53.9388 1.82292 60.0586 5.46875C66.0481 9.11459 70.7682 13.9649 74.2187 20.0196C77.6692 26.0092 79.3945 32.5196 79.3945 39.5508C79.3945 45.28 78.0924 50.6185 75.4882 55.5664C72.8841 60.5144 69.7916 64.5183 66.2109 67.5782C70.052 71.4193 73.0468 75.879 75.1953 80.9571C77.3437 86.0352 78.4179 91.3737 78.4179 96.9727C78.4179 104.72 76.5625 111.784 72.8515 118.164C69.0755 124.544 64.0299 129.655 57.7148 133.496C51.3997 137.272 44.3684 139.16 36.621 139.16ZM39.6484 23.7305H24.414V55.1758H39.6484C44.2708 55.1758 48.0143 53.5482 50.8789 50.293C53.7434 46.9727 55.1757 43.392 55.1757 39.5508C55.1757 35.3191 53.6458 31.6407 50.5859 28.5157C47.526 25.3256 43.8802 23.7305 39.6484 23.7305ZM36.621 79.3946H24.414L24.2187 114.746H36.621C41.4388 114.746 45.5729 112.988 49.0234 109.472C52.4739 105.957 54.1992 101.79 54.1992 96.9727C54.1992 92.155 52.4739 88.0209 49.0234 84.5704C45.5729 81.1198 41.4388 79.3946 36.621 79.3946ZM129.59 141.113C122.559 141.113 116.048 139.29 110.059 135.644C104.069 131.999 99.2838 127.116 95.7031 120.996C92.1875 114.811 90.4296 108.073 90.4296 100.781L90.8203 0.781246C90.8203 0.260416 91.0807 0 91.6015 0H114.063C114.583 0 114.844 0.260416 114.844 0.781246V100.781C114.844 105.273 116.276 109.114 119.141 112.305C122.005 115.43 125.488 116.992 129.59 116.992C133.887 116.992 137.468 115.43 140.332 112.305C143.197 109.114 144.629 105.273 144.629 100.781V0.781246C144.629 0.260416 144.889 0 145.41 0H167.871C168.392 0 168.652 0.260416 168.652 0.781246L169.043 100.781C169.043 108.138 167.285 114.909 163.77 121.094C160.189 127.213 155.436 132.096 149.512 135.742C143.587 139.323 136.947 141.113 129.59 141.113ZM208.203 139.16H185.547C185.026 139.16 184.766 138.834 184.766 138.183L185.156 0.781246C185.156 0.260416 185.417 0 185.938 0H226.367C233.594 0 240.235 1.75782 246.289 5.27344C252.344 8.78907 257.162 13.5092 260.742 19.4336C264.388 25.3581 266.211 32.0638 266.211 39.5508C266.211 44.4336 265.462 48.8607 263.965 52.8321C262.468 56.8034 260.71 60.1563 258.692 62.8907C256.738 65.625 254.948 67.6433 253.32 68.9454C260.547 76.9532 264.16 86.3607 264.16 97.168L264.356 138.183C264.356 138.834 264.03 139.16 263.379 139.16H240.723C240.202 139.16 239.942 138.965 239.942 138.574V97.168C239.942 92.3503 238.249 88.1836 234.863 84.668C231.478 81.1524 227.311 79.3946 222.363 79.3946H209.18L208.985 138.183C208.985 138.834 208.724 139.16 208.203 139.16ZM226.367 23.9258H209.18V55.3711H226.367C230.469 55.3711 234.115 53.8412 237.305 50.7813C240.56 47.7214 242.188 43.9779 242.188 39.5508C242.188 35.3191 240.625 31.6732 237.5 28.6133C234.375 25.4883 230.664 23.9258 226.367 23.9258ZM303.028 139.16H283.008C281.966 139.16 281.445 138.704 281.445 137.793L281.25 1.5625C281.25 0.520836 281.771 0 282.813 0H300.879L334.668 78.8086L333.692 1.5625C333.692 0.520836 334.278 0 335.449 0H355.274C356.055 0 356.445 0.520836 356.445 1.5625L356.641 137.988C356.641 138.769 356.315 139.16 355.664 139.16H338.086L303.418 65.5274L304.883 137.598C304.883 138.639 304.264 139.16 303.028 139.16ZM23.4375 291.16H0.781254C0.260414 291.16 0 290.9 0 290.379V267.722C0 267.202 0.260414 266.941 0.781254 266.941H23.4375C23.9583 266.941 24.2187 267.202 24.2187 267.722V290.379C24.2187 290.9 23.9583 291.16 23.4375 291.16ZM77.4414 293.113C70.2148 293.113 63.6067 291.29 57.6171 287.644C51.6927 283.999 46.9726 279.116 43.457 272.996C40.0065 266.811 38.2812 259.943 38.2812 252.39L38.4765 189.988C38.4765 182.566 40.1692 175.861 43.5546 169.871C46.9401 163.816 51.595 158.966 57.5195 155.32C63.5091 151.609 70.1497 149.754 77.4414 149.754C84.8632 149.754 91.4713 151.544 97.2656 155.125C103.125 158.706 107.78 163.556 111.231 169.676C114.746 175.73 116.504 182.501 116.504 189.988V199.168C116.504 199.689 116.244 199.949 115.723 199.949H93.2617C92.7408 199.949 92.4804 199.689 92.4804 199.168V189.988C92.4804 185.561 91.0481 181.752 88.1836 178.562C85.319 175.372 81.7382 173.777 77.4414 173.777C72.6888 173.777 69.0429 175.405 66.5039 178.66C63.9648 181.915 62.6953 185.691 62.6953 189.988V252.39C62.6953 257.273 64.1276 261.277 66.9921 264.402C69.8567 267.462 73.3398 268.992 77.4414 268.992C81.7382 268.992 85.319 267.299 88.1836 263.914C91.0481 260.463 92.4804 256.622 92.4804 252.39V243.113C92.4804 242.592 92.7408 242.332 93.2617 242.332H115.918C116.439 242.332 116.699 242.592 116.699 243.113V252.39C116.699 259.877 114.942 266.713 111.426 272.898C107.845 279.018 103.125 283.933 97.2656 287.644C91.4062 291.29 84.7981 293.113 77.4414 293.113ZM168.262 293.113C161.166 293.113 154.623 291.29 148.633 287.644C142.708 283.999 137.923 279.148 134.278 273.094C130.697 266.974 128.906 260.268 128.906 252.976L129.102 189.598C129.102 182.176 130.892 175.502 134.473 169.578C137.988 163.588 142.741 158.803 148.731 155.222C154.72 151.577 161.231 149.754 168.262 149.754C175.554 149.754 182.097 151.544 187.891 155.125C193.75 158.706 198.438 163.523 201.953 169.578C205.534 175.568 207.324 182.241 207.324 189.598L207.52 252.976C207.52 260.268 205.762 266.941 202.246 272.996C198.666 279.116 193.913 283.999 187.988 287.644C182.064 291.29 175.488 293.113 168.262 293.113ZM168.262 268.992C172.298 268.992 175.814 267.364 178.809 264.109C181.804 260.789 183.301 257.078 183.301 252.976L183.106 189.598C183.106 185.17 181.706 181.427 178.906 178.367C176.107 175.307 172.559 173.777 168.262 173.777C164.16 173.777 160.645 175.275 157.715 178.269C154.785 181.264 153.32 185.04 153.32 189.598V252.976C153.32 257.338 154.785 261.114 157.715 264.305C160.645 267.43 164.16 268.992 168.262 268.992ZM259.473 290.965L223.633 291.16C222.982 291.16 222.656 290.834 222.656 290.183L223.047 152.781C223.047 152.26 223.307 152 223.828 152L261.231 151.805C268.652 151.609 275.358 153.302 281.348 156.883C287.402 160.463 292.22 165.314 295.801 171.433C299.447 177.488 301.27 184.194 301.27 191.551V248.972C301.27 256.655 299.414 263.686 295.703 270.066C291.927 276.381 286.914 281.427 280.664 285.203C274.414 288.914 267.35 290.834 259.473 290.965ZM261.231 175.73L247.266 175.926L247.07 266.551H259.473C264.421 266.551 268.587 264.825 271.973 261.375C275.358 257.924 277.051 253.79 277.051 248.972V191.355C277.051 187.124 275.488 183.445 272.363 180.32C269.238 177.13 265.528 175.6 261.231 175.73ZM382.422 291.16H317.774C317.253 291.16 316.992 290.834 316.992 290.183L317.188 152.781C317.188 152.26 317.448 152 317.969 152H382.227C382.748 152 383.008 152.325 383.008 152.976V175.34C383.008 175.861 382.748 176.121 382.227 176.121H341.211V207.371H382.227C382.748 207.371 383.008 207.631 383.008 208.152L383.203 230.808C383.203 231.329 382.943 231.59 382.422 231.59H341.211V266.551H382.422C382.943 266.551 383.203 266.876 383.203 267.527V290.379C383.203 290.9 382.943 291.16 382.422 291.16ZM434.961 293.113C427.865 293.113 421.322 291.29 415.332 287.644C409.408 283.999 404.655 279.148 401.074 273.094C397.559 266.974 395.801 260.268 395.801 252.976V243.797C395.801 243.081 396.126 242.722 396.778 242.722H419.238C419.759 242.722 420.02 243.081 420.02 243.797V252.976C420.02 257.338 421.485 261.114 424.414 264.305C427.344 267.43 430.86 268.992 434.961 268.992C439.128 268.992 442.676 267.397 445.606 264.207C448.535 260.952 450 257.208 450 252.976C450 248.094 446.81 243.829 440.43 240.183C439.388 239.532 438.021 238.751 436.328 237.84C434.701 236.863 432.748 235.756 430.469 234.519C428.19 233.282 425.977 232.078 423.828 230.906C421.68 229.669 419.597 228.497 417.578 227.39C410.287 223.094 404.85 217.722 401.27 211.277C397.754 204.767 395.996 197.475 395.996 189.402C395.996 181.98 397.819 175.275 401.465 169.285C405.111 163.361 409.863 158.673 415.723 155.222C421.647 151.707 428.06 149.949 434.961 149.949C442.057 149.949 448.568 151.707 454.492 155.222C460.417 158.803 465.137 163.556 468.652 169.48C472.233 175.405 474.024 182.045 474.024 189.402V205.808C474.024 206.329 473.763 206.59 473.242 206.59H450.781C450.261 206.59 450 206.329 450 205.808L449.805 189.402C449.805 184.715 448.34 180.906 445.41 177.976C442.481 175.047 438.998 173.582 434.961 173.582C430.86 173.582 427.344 175.144 424.414 178.269C421.485 181.394 420.02 185.105 420.02 189.402C420.02 193.764 420.931 197.41 422.754 200.34C424.642 203.269 428.06 206.069 433.008 208.738C433.529 208.999 434.733 209.65 436.621 210.691C438.509 211.733 440.593 212.905 442.871 214.207C445.215 215.444 447.331 216.583 449.219 217.625C451.107 218.601 452.246 219.187 452.637 219.383C459.278 223.094 464.518 227.651 468.36 233.055C472.266 238.458 474.219 245.099 474.219 252.976C474.219 260.594 472.461 267.43 468.945 273.484C465.365 279.539 460.612 284.324 454.688 287.84C448.763 291.355 442.188 293.113 434.961 293.113Z"
              fill="white"
            />
          </svg>
        </div>

        <div v-if="tenantsStore.tenants.length > 1">
          <button
            @click="dropdownOpen = !dropdownOpen"
            class="w-full px-4 py-2 text-left bg-base-100 text-base-content rounded-md hover:bg-base-200 focus:outline-none focus:bg-base-200 flex justify-between items-center"
          >
            <span class="truncate">{{
              activeTenant ? activeTenant.name : $t("sidebar.selectTenant")
            }}</span>
            <font-awesome-icon
              :icon="['fas', 'chevron-down']"
              class="w-5 h-5"
            />
          </button>
          <div
            v-show="dropdownOpen"
            class="absolute right-0 w-full mt-2 py-2 bg-base-100 rounded-md shadow-xl z-20"
          >
            <a
              v-for="tenant in tenantsStore.tenants"
              :key="tenant.id"
              @click="selectTenant(tenant)"
              href="#"
              class="block px-4 py-2 text-sm text-base-content hover:bg-base-200"
            >
              {{ tenant.name }}
            </a>
          </div>
        </div>
        <div v-else-if="tenantsStore.tenants.length === 1" class="px-4 py-2">
          <span class="font-semibold">{{ tenantsStore.tenants[0].name }}</span>
        </div>
      </div>

      <div class="flex flex-col justify-between flex-1 mt-6">
        <nav v-if="activeTenant" @click="$emit('close-sidebar')">
          <router-link
            :to="{
              name: 'TenantSources',
              params: { tenantId: activeTenant.id },
            }"
            class="flex items-center px-4 py-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'database']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.sources") }}
          </router-link>
          <router-link
            :to="{
              name: 'TenantSettings',
              params: { tenantId: activeTenant.id },
            }"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'sliders']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.configuration") }}
          </router-link>
          <router-link
            :to="{
              name: 'TenantFineTune',
              params: { tenantId: activeTenant.id },
            }"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'flask-vial']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.fineTune") }}
          </router-link>
          <router-link
            :to="{ name: 'Analytics', params: { tenantId: activeTenant.id } }"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'chart-line']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.analytics") }}
          </router-link>
          <router-link
            :to="{ name: 'ChatLogs', params: { tenantId: activeTenant.id } }"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'history']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.chatLogs") }}
          </router-link>
          <a
            :href="`/chat/${activeTenant.id}`"
            target="_blank"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'comments']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.chatbot") }}
          </a>
        </nav>
        <div v-else class="text-center text-neutral-content opacity-50">
          <p>{{ $t("sidebar.noTenantSelected") }}</p>
        </div>

        <div @click="$emit('close-sidebar')">
          <h3
            class="px-4 mb-2 text-xs font-semibold uppercase tracking-wider opacity-50"
          >
            {{ $t("sidebar.settings") }}
          </h3>
          <router-link
            to="/profile"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon :icon="['fas', 'user']" class="w-5 h-5 mr-3" />
            {{ $t("sidebar.profile") }}
          </router-link>
          <router-link
            to="/manage-tenants"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'list-check']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.manageTenants") }}
          </router-link>
          <router-link
            to="/subscription"
            class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'credit-card']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.subscription") }}
          </router-link>
          <button
            @click="handleLogout"
            class="w-full flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus"
          >
            <font-awesome-icon
              :icon="['fas', 'arrow-right-from-bracket']"
              class="w-5 h-5 mr-3"
            />
            {{ $t("sidebar.logout") }}
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { useTenantsStore } from "../stores/tenants";
import { useAuthStore } from "../stores/auth";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";

defineProps({
  isOpen: Boolean,
});

defineEmits(["close-sidebar"]);

const tenantsStore = useTenantsStore();
const authStore = useAuthStore();
const router = useRouter();
const { t } = useI18n();

const dropdownOpen = ref(false);
const activeTenant = computed(() => tenantsStore.currentTenant);

onMounted(() => {
  tenantsStore.fetchTenants();
});

watch(
  () => [tenantsStore.tenants, router.currentRoute.value.params.tenantId],
  ([newTenants, tenantId]) => {
    if (tenantId) {
      const tenant = newTenants.find((t) => t.id === tenantId);
      if (tenant) {
        tenantsStore.selectTenant(tenant);
      }
    } else if (newTenants.length === 1) {
      tenantsStore.selectTenant(newTenants[0]);
    }
  },
  { immediate: true, deep: true }
);

const selectTenant = (tenant) => {
  dropdownOpen.value = false;
  router.push({ name: "TenantSettings", params: { tenantId: tenant.id } });
};

const handleLogout = async () => {
  await authStore.logout();
  router.push("/login");
};
</script>
