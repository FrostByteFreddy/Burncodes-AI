<template>
  <AuthLayout :tagline="$t('auth.taglineLogin')">
    <div>
      <h1 class="auth-title">{{ $t('auth.login.title') }}</h1>
      <p class="auth-sub">
        {{ $t('auth.login.noAccount') }}
        <router-link to="/signup">{{ $t('auth.login.signupLink') }}</router-link>
      </p>
    </div>

    <form class="auth-fields" @submit.prevent="handleLogin">
      <BcTextInput v-model="email" type="email" :label="$t('auth.login.email')" required autocomplete="email" />
      <BcTextInput v-model="password" type="password" :label="$t('auth.login.password')" required autocomplete="current-password" />
      <BcNotice v-if="errorMessage" tone="error" :title="errorMessage" />
      <BcButton type="submit" variant="brand" size="lg" block :loading="loading">{{ $t('auth.login.submit') }}</BcButton>
    </form>
  </AuthLayout>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../stores/auth';
import AuthLayout from '../components/AuthLayout.vue';
import { BcButton, BcNotice, BcTextInput } from '../components/ui';

const { t } = useI18n();
const authStore = useAuthStore();
const email = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    await authStore.login(email.value, password.value);
  } catch (error) {
    errorMessage.value = error.message || t('auth.unknownError');
  } finally {
    loading.value = false;
  }
};
</script>
