<template>
  <BcPanel as="section"  >
    <h2 class="panel-title">{{ $t('settings.profile.title') }}</h2>
    <p class="panel-sub">{{ $t('settings.profile.sub') }}</p>

    <div v-if="!authStore.user" class="cfg-fields ghost-stack" aria-busy="true">
      <span v-for="n in 4" :key="n" class="ghost" style="height: 40px"></span>
    </div>

    <form v-else class="cfg-fields" @submit.prevent="save">
      <div class="cfg-grid">
        <div>
          <Label for="p-first" class="mb-2">{{ $t('profile.first_name') }}</Label>
          <Input id="p-first" v-model="form.first_name" type="text"  autocomplete="given-name" />
        </div>
        <div>
          <Label for="p-last" class="mb-2">{{ $t('profile.last_name') }}</Label>
          <Input id="p-last" v-model="form.last_name" type="text"  autocomplete="family-name" />
        </div>
      </div>
      <div>
        <Label for="p-email" class="mb-2">{{ $t('profile.email') }}</Label>
        <Input id="p-email" :model-value="authStore.user.email" type="email"  disabled />
        <p class="field-hint">{{ $t('settings.profile.emailHint') }}</p>
      </div>
      <div class="cfg-grid">
        <div>
          <Label for="p-phone" class="mb-2">{{ $t('profile.phone_number') }}</Label>
          <Input id="p-phone" v-model="form.phone_number" type="tel"  autocomplete="tel" />
        </div>
        <div>
          <Label for="p-lang" class="mb-2">{{ $t('settings.profile.language') }}</Label>
          <NativeSelect id="p-lang" v-model="form.language" >
            <NativeSelectOption value="de">Deutsch</NativeSelectOption>
            <NativeSelectOption value="en">English</NativeSelectOption>
            <NativeSelectOption value="fr">Français</NativeSelectOption>
          </NativeSelect>
          <p class="field-hint">{{ $t('settings.profile.languageHint') }}</p>
        </div>
      </div>
      <div class="page-actions">
        <BcButton variant="primary" type="submit"  :disabled="saving">
          <font-awesome-icon v-if="saving" :icon="['fas', 'spinner']" class="animate-spin" />
          {{ $t('settings.save') }}
        </BcButton>
      </div>
    </form>
  </BcPanel>
</template>

<script setup>
import { BcButton, BcPanel } from '@/components/ui';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';
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
