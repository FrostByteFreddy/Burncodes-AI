<template>
  <div>
    <div class="flex justify-between items-center mb-8 border-b border-base-200/50 pb-6">
      <h3 class="text-2xl font-bold text-base-content flex items-center">
        <font-awesome-icon
          :icon="['fas', 'wand-magic-sparkles']"
          class="mr-3 text-primary"
        />
        {{ $t("tenant.fineTune.title") }}
      </h3>
      <button
        @click="isModalOpen = true"
        class="btn btn-primary rounded-xl px-6 shadow-md hover:shadow-lg transition-all duration-300"
      >
        <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
        {{ $t("tenant.fineTune.addRule") || 'Add Rule' }}
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="(rule, index) in rules"
        :key="index"
        :class="[
          'p-6 rounded-xl flex flex-col transition-all duration-300 shadow-sm',
          rule.isEditing
            ? 'bg-base-100 ring-2 ring-primary shadow-lg border-transparent relative z-10'
            : 'bg-base-100 border border-base-200/50 hover:shadow-md hover:border-base-300/50',
        ]"
      >
        <div class="flex-grow space-y-4">
          <input
            v-model="rule.trigger"
            type="text"
            :id="`trigger-${index}`"
            :placeholder="$t('tenant.fineTune.trigger.placeholder')"
            :disabled="!rule.isEditing"
            :class="[
              'w-full p-3 mt-1 rounded-xl text-lg font-bold focus:outline-none transition-shadow',
              rule.isEditing
                ? 'bg-base-200 border-none focus:ring-2 focus:ring-primary/50'
                : 'bg-transparent border-transparent text-base-content px-0',
            ]"
          />

          <div>
            <AutoGrowTextarea
              v-model="rule.instruction"
              :id="`instruction-${index}`"
              rows="1"
              :placeholder="$t('tenant.fineTune.instruction.placeholder')"
              :disabled="!rule.isEditing"
              :class="[
                'w-full p-3 mt-1 rounded-xl focus:outline-none transition-shadow',
                rule.isEditing
                  ? 'bg-base-200 border-none focus:ring-2 focus:ring-primary/50'
                  : 'bg-transparent border-transparent text-base-content/70 px-0 resize-none',
              ]"
            />
          </div>
        </div>

        <div class="flex justify-end items-center pt-3 mt-auto space-x-1">
          <template v-if="rule.isEditing">
            <button
              @click="saveEditedRule(rule)"
              class="btn btn-ghost btn-xs text-success"
            >
              <font-awesome-icon :icon="['fas', 'check']" class="h-4 w-4" />
            </button>
            <button
              @click="cancelEditing(index)"
              class="btn btn-ghost btn-xs"
            >
              <font-awesome-icon :icon="['fas', 'xmark']" class="h-4 w-4" />
            </button>
          </template>
          <template v-else>
            <button
              @click="startEditing(rule, index)"
              class="btn btn-ghost btn-xs"
            >
              <font-awesome-icon :icon="['fas', 'pen']" class="h-4 w-4" />
            </button>
            <button
              @click="removeRule(index)"
              class="btn btn-ghost btn-xs text-error"
            >
              <font-awesome-icon :icon="['fas', 'trash']" class="h-4 w-4" />
            </button>
          </template>
        </div>
      </div>
    </div>

    <p v-if="rules.length === 0" class="text-base-content/50 text-center py-8">
      {{ $t("tenant.fineTune.noRules") }}
    </p>
  </div>

  <Transition name="fade">
    <div
      v-if="isModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      @click="closeModal"
    >
      <div
        class="bg-base-100 rounded-2xl shadow-2xl w-full max-w-md p-6 sm:p-8 m-4 border border-base-200/50"
        @click.stop
      >
        <div class="flex justify-between items-center mb-6 border-b border-base-200/50 pb-4">
          <h3 class="text-xl font-bold text-base-content">
            {{ $t("tenant.fineTune.addRule") }}
          </h3>
          <button
            @click="closeModal"
            class="btn btn-ghost btn-circle btn-sm text-base-content/50 hover:bg-base-200 transition-colors"
          >
            <font-awesome-icon :icon="['fas', 'xmark']" class="h-4 w-4" />
          </button>
        </div>
        <form @submit.prevent="addRule" class="space-y-6">
          <div>
            <label
              for="new-trigger"
              class="block text-sm font-medium text-base-content mb-2"
              >{{ $t("tenant.fineTune.trigger.label") }}</label
            >
            <input
              v-model="newRule.trigger"
              type="text"
              id="new-trigger"
              :placeholder="$t('tenant.fineTune.trigger.example')"
              class="w-full p-3 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
            />
          </div>
          <div>
            <label
              for="new-instruction"
              class="block text-sm font-medium text-base-content mb-2"
              >{{ $t("tenant.fineTune.instruction.label") }}</label
            >
            <AutoGrowTextarea
              v-model="newRule.instruction"
              id="new-instruction"
              rows="3"
              :placeholder="$t('tenant.fineTune.instruction.example')"
              class="w-full p-3 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none"
            />
          </div>
          <div class="flex justify-end pt-4 space-x-3 border-t border-base-200/50 mt-6">
            <button
              type="button"
              @click="closeModal"
              class="btn btn-ghost rounded-xl px-6"
            >
              {{ $t("tenant.fineTune.actions.cancel") }}
            </button>
            <button
              type="submit"
              class="btn btn-primary rounded-xl px-6 shadow-md"
            >
              {{ $t("tenant.fineTune.actions.add") }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from "vue";
import { useTenantsStore } from "../../stores/tenants";
import { useToast } from "../../composables/useToast";
import AutoGrowTextarea from "../AutoGrowTextarea.vue";

import { useI18n } from "vue-i18n";

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();

const isModalOpen = ref(false);
const rules = ref([]);
const newRule = ref({ trigger: "", instruction: "" });

// A temporary store for the rule's state before editing, in case of cancellation
let originalRuleState = null;

watch(
  () => tenantsStore.currentTenant,
  (newTenant) => {
    if (newTenant && newTenant.fine_tune_rules) {
      // Add the isEditing flag to each rule when loading
      rules.value = JSON.parse(JSON.stringify(newTenant.fine_tune_rules)).map(
        (rule) => ({
          ...rule,
          isEditing: false,
        })
      );
    } else {
      rules.value = [];
    }
  },
  { immediate: true, deep: true }
);

const startEditing = (rule, index) => {
  // Before editing, store a copy of the current rule state
  originalRuleState = JSON.parse(JSON.stringify(rule));
  rule.isEditing = true;
};

const cancelEditing = (index) => {
  // Restore the original state and exit editing mode
  if (originalRuleState) {
    rules.value[index] = originalRuleState;
    rules.value[index].isEditing = false;
    originalRuleState = null;
  }
};

const saveEditedRule = async (rule) => {
  rule.isEditing = false;
  originalRuleState = null; // Clear the backup state
  await saveRules(); // Use the existing central save function
};

const closeModal = () => {
  isModalOpen.value = false;
  newRule.value = { trigger: "", instruction: "" };
};

// A generic function to save the current state of rules to the backend
const saveRules = async () => {
  if (tenantsStore.currentTenant) {
    // Create a "clean" version of rules without the isEditing flag for the backend
    const rulesToSave = rules.value.map(({ isEditing, ...rest }) => rest);
    const updateData = { fine_tune_rules: rulesToSave };
    try {
      await tenantsStore.updateTenant(
        tenantsStore.currentTenant.id,
        updateData
      );
      addToast(t("tenant.fineTune.actions.saveSuccess"), "success");
      return true; // Indicate success
    } catch (error) {
      addToast(t("tenant.fineTune.actions.saveFailed"), "error");
      return false; // Indicate failure
    }
  }
  return false;
};

const addRule = async () => {
  if (newRule.value.trigger.trim() && newRule.value.instruction.trim()) {
    rules.value.push({ ...newRule.value, isEditing: false });
    const success = await saveRules();
    if (success) {
      closeModal();
    } else {
      rules.value.pop();
    }
  }
};

const removeRule = async (index) => {
  const ruleBackup = rules.value[index];
  rules.value.splice(index, 1);
  const success = await saveRules();
  if (!success) {
    rules.value.splice(index, 0, ruleBackup);
  }
};
</script>
