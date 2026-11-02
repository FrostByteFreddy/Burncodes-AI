<template>
  <BcDialog open :title="$t('modals.sessionExpired.title')" :confirm-label="$t('modals.sessionExpired.logout')" :cancel-label="false" @confirm="authStore.logout()">
    {{ $t('modals.sessionExpired.message') }}
  </BcDialog>
</template>

<script setup>
import { useAuthStore } from '../stores/auth';
import { BcDialog } from './ui';

const authStore = useAuthStore();
</script>
