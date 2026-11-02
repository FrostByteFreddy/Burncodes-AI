<template>
  <BcPanel as="section"  class="dz" :title="$t('settings.danger.title')" :description="$t('settings.danger.sub')">
    <ul class="dz-list">
      <li>{{ $t('settings.danger.chatbots') }}</li>
      <li>{{ $t('settings.danger.balance') }}</li>
      <li>{{ $t('settings.danger.subscription') }}</li>
    </ul>

    <form class="cfg-fields" @submit.prevent="remove">
      <Field>
        <FieldLabel for="dz-email">{{ $t('settings.danger.typeEmail', { email: authStore.user?.email }) }}</FieldLabel>
        <Input id="dz-email" v-model="email" type="email"  autocomplete="off" />
      </Field>
      <Field>
        <FieldLabel for="dz-pw">{{ $t('profile.security.currentPassword') }}</FieldLabel>
        <Input id="dz-pw" v-model="password" type="password"  autocomplete="current-password" />
      </Field>
      <div class="page-actions">
        <button type="submit" class="dz-btn" :disabled="!canDelete || deleting">
          <font-awesome-icon :icon="deleting ? ['fas', 'spinner'] : ['fas', 'trash-alt']" :class="{ 'animate-spin': deleting }" />
          {{ $t('settings.danger.delete') }}
        </button>
      </div>
    </form>
  </BcPanel>
</template>

<script setup>
import { Field, FieldLabel } from '@/components/ui/field';
import { BcPanel } from '@/components/ui';
import { Input } from '@/components/ui/input';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import apiClient from '@/utils/api';
import { useAuthStore } from '@/stores/auth';
import { useToast } from '@/composables/useToast';

const authStore = useAuthStore();
const router = useRouter();
const { addToast } = useToast();
const { t } = useI18n();
const email = ref('');
const password = ref('');
const deleting = ref(false);

const canDelete = computed(() =>
  !!password.value && email.value.trim().toLowerCase() === (authStore.user?.email || '').toLowerCase()
);

const remove = async () => {
  if (!canDelete.value) return;
  deleting.value = true;
  try {
    await apiClient.delete('/auth/account', { data: { confirm_email: email.value.trim(), password: password.value } });
    await authStore.logout();
    router.push('/login');
  } catch (e) {
    addToast(e.response?.data?.error || t('settings.danger.failed'), 'error');
    deleting.value = false;
  }
};
</script>

<style scoped>
.dz { border-color: rgba(255, 107, 107, 0.45); }
.dz-list { margin: 12px 0 0; padding-left: 16px; display: flex; flex-direction: column; gap: 4px; font-size: var(--text-sm); color: var(--surface-text); max-width: var(--measure); }
.dz-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: var(--radius-md);
  border: none; background: var(--status-error); color: var(--on-status-error); font: inherit; font-weight: 700; cursor: pointer;
}
.dz-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
