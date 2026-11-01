<template>
  <BcPanel as="section"  >
    <h2 class="panel-title">{{ $t('settings.security.passwordTitle') }}</h2>
    <form class="cfg-fields" @submit.prevent="changePassword">
      <div>
        <Label for="s-current" class="mb-2">{{ $t('profile.security.currentPassword') }}</Label>
        <Input id="s-current" v-model="pw.current" type="password"  autocomplete="current-password" required />
      </div>
      <div class="cfg-grid">
        <div>
          <Label for="s-new" class="mb-2">{{ $t('profile.security.newPassword') }}</Label>
          <Input id="s-new" v-model="pw.next" type="password"  autocomplete="new-password" minlength="8" required />
          <p class="field-hint">{{ $t('settings.security.passwordHint') }}</p>
        </div>
        <div>
          <Label for="s-confirm" class="mb-2">{{ $t('profile.security.confirmPassword') }}</Label>
          <Input id="s-confirm" v-model="pw.confirm" type="password"  autocomplete="new-password" minlength="8" required />
          <p v-if="pw.confirm && pw.confirm !== pw.next" class="field-hint field-hint--warn">{{ $t('profile.security.passwordMismatch') }}</p>
        </div>
      </div>
      <div class="page-actions">
        <BcButton variant="primary" type="submit"  :disabled="savingPw || pw.confirm !== pw.next">
          <font-awesome-icon v-if="savingPw" :icon="['fas', 'spinner']" class="animate-spin" />
          {{ $t('profile.security.updatePassword') }}
        </BcButton>
      </div>
    </form>
  </BcPanel>

  <BcPanel as="section"  >
    <h2 class="panel-title">{{ $t('settings.security.sessionsTitle') }}</h2>
    <p class="panel-sub">{{ $t('settings.security.sessionsSub') }}</p>
    <div class="page-actions" style="margin-top: 16px">
      <BcButton variant="secondary" type="button"  :disabled="signingOut" @click="signOutEverywhere">
        <font-awesome-icon :icon="['fas', 'right-from-bracket']" /> {{ $t('settings.security.signOutAll') }}
      </BcButton>
    </div>
  </BcPanel>
</template>

<script setup>
import { BcButton, BcPanel } from '@/components/ui';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { supabase } from '@/supabase';
import { useAuthStore } from '@/stores/auth';
import { useToast } from '@/composables/useToast';

const authStore = useAuthStore();
const router = useRouter();
const { addToast } = useToast();
const { t } = useI18n();

const pw = ref({ current: '', next: '', confirm: '' });
const savingPw = ref(false);
const signingOut = ref(false);

const changePassword = async () => {
  if (pw.value.next !== pw.value.confirm) return;
  savingPw.value = true;
  try {
    await authStore.changePassword(pw.value.current, pw.value.next);
    addToast(t('profile.security.success'), 'success');
    pw.value = { current: '', next: '', confirm: '' };
  } catch (e) { addToast(e.message || t('profile.security.error'), 'error'); }
  finally { savingPw.value = false; }
};

// Revokes every session of this account: other devices can't renew their
// sign-in and are logged out within the hour at most (when their current
// access token expires); our API refuses them right away.
const signOutEverywhere = async () => {
  signingOut.value = true;
  const { error } = await supabase.auth.signOut({ scope: 'global' });
  if (error && error.code !== 'session_not_found') {
    addToast(t('settings.security.signOutFailed'), 'error');
    signingOut.value = false;
    return;
  }
  await authStore.logout();
  router.push('/login');
};
</script>
