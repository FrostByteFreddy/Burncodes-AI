<template>
  <div>
    <div
      v-if="tenantsStore.currentTenant"
      class="mb-8"
    >
      <h1 class="text-4xl font-bold flex items-center text-base-content">
        <font-awesome-icon :icon="['fas', 'cogs']" class="mr-3 text-primary opacity-80" />
        {{ tenantsStore.currentTenant.name }}
      </h1>
      <p class="text-base-content/60 mt-2 text-lg">{{ $t("tenant.subtitle") }}</p>
    </div>
    <div v-else-if="tenantsStore.loading" class="text-center p-10 text-base-content/60">
      <p class="animate-pulse">{{ $t("tenant.loading") }}</p>
    </div>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, watch } from "vue";
import { useTenantsStore } from "../stores/tenants";
import { useRoute } from "vue-router";

const tenantsStore = useTenantsStore();
const route = useRoute();

onMounted(() => {
  tenantsStore.fetchTenant(route.params.tenantId);
});

// When switching between tenants, fetch the new tenant's data
watch(
  () => route.params.tenantId,
  (newId) => {
    if (newId) {
      tenantsStore.fetchTenant(newId);
    }
  }
);
</script>

