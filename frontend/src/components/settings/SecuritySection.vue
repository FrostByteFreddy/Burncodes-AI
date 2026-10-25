<template>
  <section class="panel">
    <h2 class="panel-title">{{ $t('settings.security.passwordTitle') }}</h2>
    <form class="cfg-fields" @submit.prevent="changePassword">
      <div>
        <label for="s-current" class="form-field">{{ $t('profile.security.currentPassword') }}</label>
        <input id="s-current" v-model="pw.current" type="password" class="form-input" autocomplete="current-password" required />
      </div>
      <div class="cfg-grid">
        <div>
          <label for="s-new" class="form-field">{{ $t('profile.security.newPassword') }}</label>
          <input id="s-new" v-model="pw.next" type="password" class="form-input" autocomplete="new-password" minlength="8" required />
          <p class="field-hint">{{ $t('settings.security.passwordHint') }}</p>
        </div>
        <div>
          <label for="s-confirm" class="form-field">{{ $t('profile.security.confirmPassword') }}</label>
          <input id="s-confirm" v-model="pw.confirm" type="password" class="form-input" autocomplete="new-password" minlength="8" required />
          <p v-if="pw.confirm && pw.confirm !== pw.next" class="field-hint field-hint--warn">{{ $t('profile.security.passwordMismatch') }}</p>
        </div>
      </div>
      <div class="page-actions">
        <button type="submit" class="btn-action" :disabled="savingPw || pw.confirm !== pw.next">
          <font-awesome-icon v-if="savingPw" :icon="['fas', 'spinner']" class="animate-spin" />
          {{ $t('profile.security.updatePassword') }}
        </button>
      </div>
    </form>
  </section>

  <section class="panel">
    <h2 class="panel-title">{{ $t('settings.security.sessionsTitle') }}</h2>
    <p class="panel-sub">{{ $t('settings.security.sessionsSub') }}</p>
    <div class="page-actions" style="margin-top: 16px">
      <button type="button" class="btn-quiet" :disabled="signingOut" @click="signOutEverywhere">
        <font-awesome-icon :icon="['fas', 'right-from-bracket']" /> {{ $t('settings.security.signOutAll') }}
      </button>
    </div>
  </section>
</template>

<script setup>
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
