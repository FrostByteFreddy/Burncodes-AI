<template>
  <BcPanel as="section"   :title="$t('settings.profile.title')" :description="$t('settings.profile.sub')">

    <div v-if="!authStore.user" class="cfg-fields ghost-stack" aria-busy="true">
      <Skeleton v-for="n in 4" :key="n" style="height: 40px" />
    </div>

    <form v-else class="cfg-fields" @submit.prevent="save">
      <div class="cfg-grid">
        <Field>
          <FieldLabel for="p-first">{{ $t('profile.first_name') }}</FieldLabel>
          <Input id="p-first" v-model="form.first_name" type="text"  autocomplete="given-name" />
        </Field>
        <Field>
          <FieldLabel for="p-last">{{ $t('profile.last_name') }}</FieldLabel>
          <Input id="p-last" v-model="form.last_name" type="text"  autocomplete="family-name" />
        </Field>
      </div>
      <Field>
        <FieldLabel for="p-email">{{ $t('profile.email') }}</FieldLabel>
        <Input id="p-email" :model-value="authStore.user.email" type="email"  disabled />
        <FieldDescription >{{ $t('settings.profile.emailHint') }}</FieldDescription>
      </Field>
      <div class="cfg-grid">
        <Field>
          <FieldLabel for="p-phone">{{ $t('profile.phone_number') }}</FieldLabel>
          <Input id="p-phone" v-model="form.phone_number" type="tel"  autocomplete="tel" />
        </Field>
        <Field>
          <FieldLabel for="p-lang">{{ $t('settings.profile.language') }}</FieldLabel>
          <NativeSelect id="p-lang" v-model="form.language" >
            <NativeSelectOption value="de">Deutsch</NativeSelectOption>
            <NativeSelectOption value="en">English</NativeSelectOption>
            <NativeSelectOption value="fr">Français</NativeSelectOption>
          </NativeSelect>
          <FieldDescription >{{ $t('settings.profile.languageHint') }}</FieldDescription>
        </Field>
      </div>
      <div class="page-actions">
        <BcButton variant="primary" type="submit"  :disabled="saving">
          <Spinner v-if="saving" data-icon="inline-start" />
          {{ $t('settings.save') }}
        </BcButton>
      </div>
    </form>
  </BcPanel>
</template>

<script setup>
import { Spinner } from '@/components/ui/spinner';
import { Skeleton } from '@/components/ui/skeleton';
import { Field, FieldDescription, FieldLabel } from '@/components/ui/field';
import { BcButton, BcPanel } from '@/components/ui';
import { Input } from '@/components/ui/input';
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
