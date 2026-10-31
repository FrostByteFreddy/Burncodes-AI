<template>
  <AuthLayout :tagline="$t('auth.taglineSignup')">
    <div>
      <h1 class="auth-title">{{ $t('auth.signup.title') }}</h1>
      <p class="auth-sub">
        {{ $t('auth.signup.alreadyHaveAccount') }}
        <router-link to="/login">{{ $t('auth.signup.loginLink') }}</router-link>
      </p>
    </div>

    <BcNotice v-if="done" tone="success" :title="$t('auth.signup.successMessage')" />
    <form v-else class="auth-fields" @submit.prevent="handleSignup">
      <div class="auth-row">
        <BcTextInput v-model="firstName" :label="$t('auth.signup.firstName')" required autocomplete="given-name" />
        <BcTextInput v-model="lastName" :label="$t('auth.signup.lastName')" required autocomplete="family-name" />
      </div>
      <BcTextInput v-model="email" type="email" :label="$t('auth.signup.email')" required autocomplete="email" />
      <BcTextInput v-model="password" type="password" :label="$t('auth.signup.password')" required autocomplete="new-password" />
      <BcSelect v-model="language" :label="$t('auth.signup.language')" :options="LANGUAGES" />
      <BcNotice v-if="errorMessage" tone="error" :title="errorMessage" />
      <BcButton type="submit" variant="brand" size="lg" block :loading="loading">{{ $t('auth.signup.submit') }}</BcButton>
    </form>
  </AuthLayout>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../stores/auth';
import AuthLayout from '../components/AuthLayout.vue';
import { BcButton, BcNotice, BcSelect, BcTextInput } from '../components/ui';

const LANGUAGES = [{ value: 'de', label: 'Deutsch' }, { value: 'en', label: 'English' }, { value: 'fr', label: 'Français' }];

const { t, locale } = useI18n();
const authStore = useAuthStore();
const firstName = ref('');
const lastName = ref('');
const email = ref('');
const password = ref('');
// the dashboard language people already see is the likeliest choice
const language = ref(LANGUAGES.some((l) => l.value === locale.value) ? locale.value : 'de');
const loading = ref(false);
const errorMessage = ref('');
const done = ref(false);

const handleSignup = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    await authStore.signUp(email.value, password.value, firstName.value, lastName.value, language.value);
    done.value = true;
  } catch (error) {
    errorMessage.value = error.message || t('auth.unknownError');
  } finally {
    loading.value = false;
  }
};
</script>
