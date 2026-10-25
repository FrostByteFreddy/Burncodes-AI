<template>
  <section class="panel">
    <h2 class="panel-title">{{ $t('settings.profile.title') }}</h2>
    <p class="panel-sub">{{ $t('settings.profile.sub') }}</p>

    <div v-if="!authStore.user" class="cfg-fields ghost-stack" aria-busy="true">
      <span v-for="n in 4" :key="n" class="ghost" style="height: 40px"></span>
    </div>

    <form v-else class="cfg-fields" @submit.prevent="save">
      <div class="cfg-grid">
        <div>
          <label for="p-first" class="form-field">{{ $t('profile.first_name') }}</label>
          <input id="p-first" v-model="form.first_name" type="text" class="form-input" autocomplete="given-name" />
        </div>
        <div>
          <label for="p-last" class="form-field">{{ $t('profile.last_name') }}</label>
          <input id="p-last" v-model="form.last_name" type="text" class="form-input" autocomplete="family-name" />
        </div>
      </div>
      <div>
        <label for="p-email" class="form-field">{{ $t('profile.email') }}</label>
        <input id="p-email" :value="authStore.user.email" type="email" class="form-input" disabled />
        <p class="field-hint">{{ $t('settings.profile.emailHint') }}</p>
      </div>
      <div class="cfg-grid">
        <div>
          <label for="p-phone" class="form-field">{{ $t('profile.phone_number') }}</label>
          <input id="p-phone" v-model="form.phone_number" type="tel" class="form-input" autocomplete="tel" />
        </div>
        <div>
          <label for="p-lang" class="form-field">{{ $t('settings.profile.language') }}</label>
          <select id="p-lang" v-model="form.language" class="form-input">
            <option value="de">Deutsch</option>
            <option value="en">English</option>
            <option value="fr">Français</option>
          </select>
          <p class="field-hint">{{ $t('settings.profile.languageHint') }}</p>
        </div>
      </div>
      <div class="page-actions">
        <button type="submit" class="btn-action" :disabled="saving">
          <font-awesome-icon v-if="saving" :icon="['fas', 'spinner']" class="animate-spin" />
          {{ $t('settings.save') }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { useToast } from '@/composables/useToast';

const authStore = useAuthStore();
const { addToast } = useToast();
const { t, locale } = useI18n();
const saving = ref(false);
const form = ref({ first_name: '', last_name: '', phone_number: '', language: 'en' });

const fill = () => {
  const meta = authStore.user?.user_metadata || {};
  form.value = {
    first_name: meta.first_name || '',
    last_name: meta.last_name || '',
    phone_number: meta.phone_number || '',
    language: meta.language || locale.value || 'en',
  };
};
onMounted(async () => { if (!authStore.user) await authStore.fetchUser(); fill(); });
watch(() => authStore.user?.id, fill);

const save = async () => {
  saving.value = true;
  try {
    await authStore.updateProfile(form.value);
    locale.value = form.value.language;
    addToast(t('settings.saved'), 'success');
  } catch { addToast(t('profile.error'), 'error'); }
  finally { saving.value = false; }
};
</script>
