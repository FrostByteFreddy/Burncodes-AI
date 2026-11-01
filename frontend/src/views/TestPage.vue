<template>
  <div class="tp">
    <div class="page-head">
      <div>
        <h1 class="page-title">{{ $t('testPage.title') }}</h1>
        <p class="page-lede">{{ $t('testPage.lede') }}</p>
      </div>
    </div>

    <div v-if="!tenant" class="ghost-stack" aria-busy="true">
      <BcPanel as="section"  v-for="n in 2" :key="n" class="ghost-stack">
        <Skeleton class="ghost--title" style="width: 160px" />
        <Skeleton style="height: 44px" />
      </BcPanel>
    </div>

    <template v-else>
      <!-- The link -->
      <BcPanel as="section"   :title="$t('testPage.link.title')" :description="$t('testPage.link.sub')">
        <div class="tp-link">
          <code class="tp-link__url">{{ url }}</code>
          <div class="page-actions">
            <BcButton variant="secondary" type="button"  @click="copy">
              <font-awesome-icon :icon="['fas', copied ? 'check' : 'copy']" /> {{ copied ? $t('testPage.link.copied') : $t('testPage.link.copy') }}
            </BcButton>
            <Button as-child variant="default"><a :href="url" target="_blank" rel="noopener" class="tp-open">
              <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" /> {{ $t('testPage.link.open') }}
            </a></Button>
          </div>
        </div>
        <p v-if="tenant.is_active === false" class="tp-note tp-note--warn">
          <font-awesome-icon :icon="['fas', 'power-off']" />
          <span>{{ $t('testPage.link.off') }} <router-link :to="{ name: 'TenantOverview', params: { tenantId: tenant.id } }">{{ $t('testPage.link.offLink') }}</router-link></span>
        </p>
        <p v-else-if="tenant.test_protected" class="tp-note">
          <font-awesome-icon :icon="['fas', 'lock']" />
          <span>{{ $t('testPage.link.protected') }}</span>
        </p>
      </BcPanel>

      <!-- Password while in development -->
      <BcPanel as="section"  >
        <div class="tp-switch-row">
          <div>
            <label for="tp-protect" class="panel-title tp-label">{{ $t('testPage.password.title') }}</label>
            <CardDescription>{{ $t('testPage.password.sub') }}</CardDescription>
          </div>
          <Switch id="tp-protect" :model-value="protectOn" :disabled="saving" @update:model-value="toggle" />
        </div>

        <form v-if="editing" class="cfg-fields" @submit.prevent="savePassword">
          <Field>
            <FieldLabel for="tp-pw">{{ tenant.test_protected ? $t('testPage.password.new') : $t('testPage.password.label') }}</FieldLabel>
            <div class="tp-pw">
              <Input id="tp-pw" ref="pwInput" v-model="newPassword" :type="showPassword ? 'text' : 'password'"  minlength="6" autocomplete="new-password" />
              <BcButton variant="secondary" type="button"  :aria-pressed="showPassword" @click="showPassword = !showPassword">
                <font-awesome-icon :icon="['fas', showPassword ? 'eye-slash' : 'eye']" /> {{ showPassword ? $t('testPage.password.hide') : $t('testPage.password.show') }}
              </BcButton>
            </div>
            <FieldDescription  :class="{ 'field-hint--warn': newPassword && newPassword.length < 6 }">{{ $t('testPage.password.hint') }}</FieldDescription>
          </Field>
          <div class="page-actions">
            <BcButton variant="primary" type="submit"  :disabled="saving || newPassword.length < 6">
              <Spinner v-if="saving" data-icon="inline-start" /> {{ $t('testPage.password.save') }}
            </BcButton>
            <BcButton variant="secondary" type="button"  :disabled="saving" @click="cancelEdit">{{ $t('testPage.password.cancel') }}</BcButton>
          </div>
        </form>

        <div v-else-if="tenant.test_protected" class="tp-set">
          <p><font-awesome-icon :icon="['fas', 'check']" class="tp-set__ok" /> {{ $t('testPage.password.isSet') }}</p>
          <BcButton variant="secondary" type="button"  @click="startEdit">{{ $t('testPage.password.change') }}</BcButton>
        </div>

        <ul class="tp-notes">
          <li>{{ $t('testPage.password.widgetNote') }}</li>
          <li>{{ $t('testPage.password.shareNote') }}</li>
          <li>{{ $t('testPage.password.previewNote') }}</li>
        </ul>
      </BcPanel>
    </template>
  </div>
</template>

<script setup>
import { Switch } from '@/components/ui/switch';
import { Spinner } from '@/components/ui/spinner';
import { Skeleton } from '@/components/ui/skeleton';
import { CardDescription } from '@/components/ui/card';
import { Field, FieldDescription, FieldLabel } from '@/components/ui/field';
import { BcButton, BcPanel } from '@/components/ui';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { computed, nextTick, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useTenantsStore } from '@/stores/tenants';
import { useToast } from '@/composables/useToast';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();

const tenant = computed(() => tenantsStore.currentTenant);
const url = computed(() => `${window.location.origin}/chat/${tenant.value?.id}`);

const copied = ref(false);
const copy = async () => {
  try {
    await navigator.clipboard.writeText(url.value);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch { addToast(t('testPage.link.copyFailed'), 'error'); }
};

// ── Password ────────────────────────────────────────────────────────
const editing = ref(false);
const newPassword = ref('');
const showPassword = ref(false);
const saving = ref(false);
const pwInput = ref(null);
// The switch shows "on" while a password is being typed, before it's saved
const protectOn = computed(() => !!tenant.value?.test_protected || editing.value);

const startEdit = async () => {
  editing.value = true;
  newPassword.value = '';
  await nextTick();
  pwInput.value?.focus();
};
const cancelEdit = () => { editing.value = false; newPassword.value = ''; };

const save = async (password, message) => {
  saving.value = true;
  try {
    await apiClient.put(`/tenants/${tenant.value.id}`, { test_password: password });
    await tenantsStore.refetch(tenant.value.id);
    addToast(message, 'success');
    editing.value = false;
    newPassword.value = '';
  } catch (e) {
    addToast(e.response?.data?.error || t('tenant.settings.actions.saveFailed'), 'error');
  } finally { saving.value = false; }
};

const toggle = (on) => {
  if (on) startEdit();
  else if (editing.value && !tenant.value.test_protected) cancelEdit();
  else save(null, t('testPage.password.removed'));
};
const savePassword = () => save(newPassword.value, t('testPage.password.saved'));
</script>

<style scoped>
.tp { display: flex; flex-direction: column; gap: 20px; }

.tp-link { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-top: 16px; padding: 12px 12px 12px 16px; border-radius: var(--radius-lg); background: var(--surface-2); border: 1px solid var(--surface-3); }
.tp-link__url { flex: 1; min-width: 240px; font-family: inherit; font-size: 15px; font-weight: 600; color: var(--surface-heading); overflow-wrap: anywhere; }
.tp-open { text-decoration: none; }
.tp-note { display: flex; gap: 10px; align-items: baseline; margin-top: 14px; font-size: var(--text-sm); color: var(--surface-text); }
.tp-note svg { color: var(--surface-muted); }
.tp-note--warn, .tp-note--warn svg { color: var(--status-warning); }
.tp-note a { color: inherit; font-weight: 600; }

.tp-switch-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.tp-label { display: block; cursor: pointer; }
/* switch look shared with the Overview page */

.tp-pw { display: flex; gap: 8px; align-items: center; }
.tp-pw [data-slot=input] { flex: 1; max-width: 360px; }
.tp-set { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-top: 16px; padding: 12px 16px; border-radius: var(--radius-lg); background: var(--surface-2); font-size: 15px; color: var(--surface-heading); }
.tp-set__ok { color: var(--status-success); margin-right: 6px; }
.tp-notes { margin: 18px 0 0; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; font-size: var(--text-sm); color: var(--surface-muted); max-width: var(--measure); }

@media (prefers-reduced-motion: reduce) { .ov-switch, .ov-switch::after { transition: none; } }
</style>
