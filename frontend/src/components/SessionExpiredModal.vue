<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center"
    style="background: rgba(0,0,0,0.65); backdrop-filter: blur(4px);"
  >
    <div class="modal-box">
      <h2 class="modal-box__title">{{ $t("modals.sessionExpired.title") }}</h2>
      <p class="modal-box__body">{{ $t("modals.sessionExpired.message") }}</p>
      <button @click="onLogout" ref="logoutButton" class="modal-btn modal-btn--primary">
        {{ $t("modals.sessionExpired.logout") }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const logoutButton = ref(null);
const onLogout = () => authStore.logout();

onMounted(() => logoutButton.value?.focus());
</script>

<style scoped>
.modal-box {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 40px 32px;
  width: 100%; max-width: 400px;
  margin: 16px;
  text-align: center;
}
.modal-box__title {
  font-size: 20px; font-weight: 700;
  color: var(--surface-heading);
  margin-bottom: 12px;
}
.modal-box__body {
  font-size: 14px; color: var(--surface-muted);
  line-height: 1.6; margin-bottom: 28px;
}
.modal-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 24px; font-size: 13px; font-weight: 600;
  border: none; border-radius: var(--radius-md);
  cursor: pointer; transition: opacity var(--t-fast);
}
.modal-btn--primary { background: var(--gradient-brand); color: white; }
.modal-btn--primary:hover { opacity: 0.9; }
</style>
