<template>
  <div>
    <div class="rules-grid">
      <div v-for="(rule, index) in rules" :key="index"
        class="rule-card"
        :class="{ 'is-editing': rule.isEditing }">
        <div class="flex-grow space-y-4">
          <input v-model="rule.trigger" type="text" :id="`trigger-${index}`"
            :placeholder="$t('tenant.fineTune.trigger.placeholder')"
            :disabled="!rule.isEditing"
            class="rule-card__trigger"
            :class="{ 'is-editing': rule.isEditing }" />
          <AutoGrowTextarea v-model="rule.instruction" :id="`instruction-${index}`" rows="1"
            :placeholder="$t('tenant.fineTune.instruction.placeholder')"
            :disabled="!rule.isEditing"
            class="rule-card__instruction"
            :class="{ 'is-editing': rule.isEditing }" />
        </div>
        <div class="rule-card__actions">
          <template v-if="rule.isEditing">
            <button type="button" @click="saveEditedRule(rule)" class="btn btn-ghost btn-xs text-success">
              <font-awesome-icon :icon="['fas', 'check']" class="h-4 w-4" />
            </button>
            <button type="button" @click="cancelEditing(index)" class="btn btn-ghost btn-xs">
              <font-awesome-icon :icon="['fas', 'xmark']" class="h-4 w-4" />
            </button>
          </template>
          <template v-else>
            <button type="button" @click="startEditing(rule)" class="btn btn-ghost btn-xs">
              <font-awesome-icon :icon="['fas', 'pen']" class="h-4 w-4" />
            </button>
            <button type="button" @click="removeRule(index)" class="btn btn-ghost btn-xs text-error">
              <font-awesome-icon :icon="['fas', 'trash']" class="h-4 w-4" />
            </button>
          </template>
        </div>
      </div>
    </div>

    <p v-if="rules.length === 0" class="rules-empty">{{ $t("tenant.fineTune.noRules") }}</p>

    <AddRuleWizard
      :open="isWizardOpen"
      @close="isWizardOpen = false"
      @add-rule="addRule"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useToast } from '../../../composables/useToast';
import { useTenantsStore } from '../../../stores/tenants';
import AutoGrowTextarea from '../../AutoGrowTextarea.vue';
import AddRuleWizard from '../sources/AddRuleWizard.vue';

const tenantsStore = useTenantsStore();
const { t } = useI18n();
const { addToast } = useToast();

const rules = ref([]);
const isWizardOpen = ref(false);
let originalRuleState = null;

watch(() => tenantsStore.currentTenant, (tenant) => {
  rules.value = tenant?.fine_tune_rules
    ? JSON.parse(JSON.stringify(tenant.fine_tune_rules)).map(r => ({ ...r, isEditing: false }))
    : [];
}, { immediate: true, deep: true });

const saveRules = async () => {
  if (!tenantsStore.currentTenant) return false;
  const rulesToSave = rules.value.map(({ isEditing, ...rest }) => rest);
  try {
    await tenantsStore.updateTenant(tenantsStore.currentTenant.id, { fine_tune_rules: rulesToSave });
    addToast(t('tenant.fineTune.actions.saveSuccess'), 'success');
    return true;
  } catch {
    addToast(t('tenant.fineTune.actions.saveFailed'), 'error');
    return false;
  }
};

const startEditing   = (rule)  => { originalRuleState = JSON.parse(JSON.stringify(rule)); rule.isEditing = true; };
const cancelEditing  = (index) => { if (originalRuleState) { rules.value[index] = originalRuleState; rules.value[index].isEditing = false; originalRuleState = null; } };
const saveEditedRule = async (rule) => { rule.isEditing = false; originalRuleState = null; await saveRules(); };

const addRule = async ({ trigger, instruction }) => {
  rules.value.push({ trigger, instruction, isEditing: false });
  const ok = await saveRules();
  if (!ok) rules.value.pop();
};

const removeRule = async (index) => {
  const backup = rules.value[index];
  rules.value.splice(index, 1);
  const ok = await saveRules();
  if (!ok) rules.value.splice(index, 0, backup);
};

defineExpose({ openModal: () => { isWizardOpen.value = true; } });
</script>
