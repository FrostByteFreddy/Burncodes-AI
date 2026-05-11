<template>
    <main>
      <router-view />
    </main>
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

