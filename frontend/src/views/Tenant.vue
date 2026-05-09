<template>
  <div>
    <div
      v-if="tenantsStore.currentTenant"
      class="mb-8"
    >
      <h1 style="font-size:1.75rem;font-weight:700;display:flex;align-items:center;color:var(--surface-heading);">
        <font-awesome-icon :icon="['fas', 'cogs']" style="margin-right:0.75rem;color:var(--brand-indigo);opacity:0.9;" />
        {{ tenantsStore.currentTenant.name }}
      </h1>
      <p style="color:var(--surface-muted);margin-top:0.5rem;font-size:0.9rem;">{{ $t("tenant.subtitle") }}</p>
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

// When switching tabs/pages WITHIN the same tenant, silently refetch to guarantee fresh data
watch(
  () => route.path,
  () => {
    if (route.params.tenantId && tenantsStore.currentTenant?.id === route.params.tenantId) {
      tenantsStore.refetch(route.params.tenantId);
    }
  }
);
</script>

