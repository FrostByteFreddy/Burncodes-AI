<template>
  <BcDialog open :title="$t('modals.createTenant.title')" icon="layer-group" :confirm-label="$t('modals.createTenant.create')"
    :confirm-disabled="!name.trim()" :loading="submitting" @confirm="handleSubmit" @cancel="$emit('close')">
    <form class="ctm" @submit.prevent="handleSubmit">
      <BcTextInput v-model="name" :label="$t('modals.createTenant.name')" :hint="$t('onboarding.basics.nameHint')" required />
      <BcRadioCards v-model="audience" :legend="$t('configure.basics.audience')" :options="audienceOptions" :columns="1" />
      <BcNotice v-if="error" tone="error" :title="error" />
    </form>
  </BcDialog>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useTenantsStore } from '../stores/tenants';
import { AUDIENCES, DEFAULT_AUDIENCE, defaultsFor } from '../utils/chatbotDefaults';
import { BcDialog, BcNotice, BcRadioCards, BcTextInput } from './ui';

const emit = defineEmits(['close']);
const tenantsStore = useTenantsStore();
const router = useRouter();
const { t, locale } = useI18n();

const name = ref('');
const audience = ref(DEFAULT_AUDIENCE);
const submitting = ref(false);
const error = ref('');
const audienceOptions = computed(() => AUDIENCES.map((key) => ({
  value: key, icon: key === 'municipality' ? 'landmark' : 'store',
  title: t(`configure.basics.audiences.${key}`), description: t(`configure.basics.audiences.${key}Desc`),
})));

const handleSubmit = async () => {
  if (!name.value.trim() || submitting.value) return;
  error.value = '';
  submitting.value = true;
  try {
    const created = await tenantsStore.createTenant({ name: name.value.trim(), audience: audience.value, ...defaultsFor(locale.value) });
    emit('close');
    if (created?.id) router.push(`/tenant/${created.id}`);
  } catch {
    error.value = t('modals.createTenant.failed');
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.ctm { display: flex; flex-direction: column; gap: var(--space-5); }
</style>
