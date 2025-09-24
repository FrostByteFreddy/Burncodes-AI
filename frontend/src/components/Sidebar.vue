<template>
    <aside
        class="fixed inset-y-0 left-0 z-40 w-3/4 sm:w-64 bg-neutral text-neutral-content transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0"
        :class="isOpen ? 'translate-x-0' : '-translate-x-full'">
        <!-- <div class="md:hidden absolute top-2 -right-2">
            <button @click="$emit('close-sidebar')" class="btn btn-square btn-ghost">
                <font-awesome-icon :icon="['fas', 'times']" class="h-6 w-6" />
            </button>
        </div> -->

        <div class="flex flex-col h-screen px-4 py-8">
            <h2 class="hidden sm:block text-3xl font-semibold text-center text-primary ">BurnCodes AI</h2>

            <div class="relative mt-6">
                <div v-if="tenantsStore.tenants.length > 1">
                    <button @click="dropdownOpen = !dropdownOpen"
                        class="w-full px-4 py-2 text-left bg-base-100 text-base-content rounded-md hover:bg-base-200 focus:outline-none focus:bg-base-200 flex justify-between items-center">
                        <span class="truncate">{{ activeTenant ? activeTenant.name : 'Select a Tenant' }}</span>
                        <font-awesome-icon :icon="['fas', 'chevron-down']" class="w-5 h-5" />
                    </button>
                    <div v-show="dropdownOpen"
                        class="absolute right-0 w-full mt-2 py-2 bg-base-100 rounded-md shadow-xl z-20">
                        <a v-for="tenant in tenantsStore.tenants" :key="tenant.id" @click="selectTenant(tenant)"
                            href="#" class="block px-4 py-2 text-sm text-base-content hover:bg-base-200">
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
                    <router-link :to="{ name: 'TenantSources', params: { tenantId: activeTenant.id } }"
                        class="flex items-center px-4 py-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'database']" class="w-5 h-5 mr-3" />
                        Sources
                    </router-link>
                    <router-link :to="{ name: 'TenantSettings', params: { tenantId: activeTenant.id } }"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'sliders']" class="w-5 h-5 mr-3" />
                        Configuration
                    </router-link>
                    <router-link :to="{ name: 'TenantFineTune', params: { tenantId: activeTenant.id } }"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'flask-vial']" class="w-5 h-5 mr-3" />
                        Fine Tune
                    </router-link>
                    <router-link :to="{ name: 'Analytics', params: { tenantId: activeTenant.id } }"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'chart-line']" class="w-5 h-5 mr-3" />
                        Analytics
                    </router-link>
                    <router-link :to="{ name: 'ChatLogs', params: { tenantId: activeTenant.id } }"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'history']" class="w-5 h-5 mr-3" />
                        Chat Logs
                    </router-link>
                    <a :href="`/chat/${activeTenant.id}`" target="_blank"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'comments']" class="w-5 h-5 mr-3" />
                        Chatbot
                    </a>
                </nav>
                <div v-else class="text-center text-neutral-content opacity-50">
                    <p>Select a tenant to see management options.</p>
                </div>

                <div @click="$emit('close-sidebar')">
                    <h3 class="px-4 mb-2 text-xs font-semibold uppercase tracking-wider opacity-50">Settings</h3>
                    <router-link to="/profile"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'user']" class="w-5 h-5 mr-3" />
                        Profile
                    </router-link>
                    <router-link to="/manage-tenants"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'list-check']" class="w-5 h-5 mr-3" />
                        Manage Tenants
                    </router-link>
                    <router-link to="/subscription"
                        class="flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'credit-card']" class="w-5 h-5 mr-3" />
                        Subscription
                    </router-link>
                    <button @click="handleLogout"
                        class="w-full flex items-center px-4 py-2 mt-2 rounded-md hover:bg-neutral-focus">
                        <font-awesome-icon :icon="['fas', 'arrow-right-from-bracket']" class="w-5 h-5 mr-3" />
                        Logout
                    </button>
                </div>
            </div>
        </div>
    </aside>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

defineProps({
    isOpen: Boolean
})

defineEmits(['close-sidebar'])

const tenantsStore = useTenantsStore()
const authStore = useAuthStore()
const router = useRouter()

const dropdownOpen = ref(false)
const activeTenant = ref(null)

onMounted(() => {
    tenantsStore.fetchTenants()
});

watch(() => [tenantsStore.tenants, router.currentRoute.value.params.tenantId], ([newTenants, tenantId]) => {
    if (tenantId) {
        const tenant = newTenants.find(t => t.id === tenantId);
        if (tenant) {
            activeTenant.value = tenant;
        }
    } else if (newTenants.length === 1) {
        activeTenant.value = newTenants[0];
    } else {
        activeTenant.value = null;
    }
}, { immediate: true, deep: true });


const selectTenant = (tenant) => {
    activeTenant.value = tenant
    dropdownOpen.value = false
    router.push({ name: 'TenantSettings', params: { tenantId: tenant.id } })
}

const handleLogout = async () => {
    await authStore.logout()
    router.push('/login')
}
</script>
