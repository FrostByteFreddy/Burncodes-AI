<template>
  <BcPanel as="section"   :title="$t('settings.security.passwordTitle')">
    <form class="cfg-fields" @submit.prevent="changePassword">
      <Field>
        <FieldLabel for="s-current">{{ $t('profile.security.currentPassword') }}</FieldLabel>
        <Input id="s-current" v-model="pw.current" type="password"  autocomplete="current-password" required />
      </Field>
      <div class="cfg-grid">
        <Field>
          <FieldLabel for="s-new">{{ $t('profile.security.newPassword') }}</FieldLabel>
          <Input id="s-new" v-model="pw.next" type="password"  autocomplete="new-password" minlength="8" required />
          <FieldDescription >{{ $t('settings.security.passwordHint') }}</FieldDescription>
        </Field>
        <Field>
          <FieldLabel for="s-confirm">{{ $t('profile.security.confirmPassword') }}</FieldLabel>
          <Input id="s-confirm" v-model="pw.confirm" type="password"  autocomplete="new-password" minlength="8" required />
          <p v-if="pw.confirm && pw.confirm !== pw.next" class="field-hint field-hint--warn">{{ $t('profile.security.passwordMismatch') }}</p>
        </Field>
      </div>
      <div class="page-actions">
        <BcButton variant="primary" type="submit"  :disabled="savingPw || pw.confirm !== pw.next">
          <Spinner v-if="savingPw" data-icon="inline-start" />
          {{ $t('profile.security.updatePassword') }}
        </BcButton>
      </div>
    </form>
  </BcPanel>

  <BcPanel as="section"   :title="$t('settings.security.sessionsTitle')" :description="$t('settings.security.sessionsSub')">
    <div class="page-actions" style="margin-top: 16px">
      <BcButton variant="secondary" type="button"  :disabled="signingOut" @click="signOutEverywhere">
        <font-awesome-icon :icon="['fas', 'right-from-bracket']" /> {{ $t('settings.security.signOutAll') }}
      </BcButton>
    </div>
  </BcPanel>
</template>

<script setup>
import { Spinner } from '@/components/ui/spinner';
import { Field, FieldDescription, FieldLabel } from '@/components/ui/field';
import { BcButton, BcPanel } from '@/components/ui';
import { Input } from '@/components/ui/input';
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
