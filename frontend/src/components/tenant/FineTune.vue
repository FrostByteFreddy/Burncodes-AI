<template>
    <div class="bg-white p-6 sm:p-8 rounded-2xl shadow-lg">

        <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold text-gray-800 flex items-center">
                <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" class="mr-3 text-purple-500" />
                Fine-Tuning Rules
            </h3>
            <button @click="isModalOpen = true"
                class="inline-flex items-center p-3 rounded-full font-semibold text-white bg-purple-500 shadow-sm hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                <font-awesome-icon :icon="['fas', 'plus']" class="h-4 w-4" />
            </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="(rule, index) in rules" :key="index" :class="[
                'p-4 rounded-xl flex flex-col transition-all duration-300',
                rule.isEditing ? 'bg-white ring-2 ring-purple-500 shadow-xl' : 'bg-slate-50 border border-slate-200'
            ]">
                <div class="flex-grow space-y-3">
                    <input v-model="rule.trigger" type="text" :id="`trigger-${index}`" placeholder="Trigger"
                        :disabled="!rule.isEditing" :class="[
                            'w-full p-2 mt-1 rounded-lg text-lg font-semibold focus:outline-none',
                            rule.isEditing ? 'bg-white border-slate-300 border focus:ring-2 focus:ring-purple-400' : 'bg-transparent border-transparent text-slate-800'
                        ]" />

                    <div>
                        <AutoGrowTextarea v-model="rule.instruction" :id="`instruction-${index}`" rows="1"
                            placeholder="Instruction" :disabled="!rule.isEditing" :class="[
                                'w-full p-2 mt-1 rounded-lg focus:outline-none',
                                rule.isEditing ? 'bg-white border-slate-300 border focus:ring-2 focus:ring-purple-400' : 'bg-transparent border-transparent text-slate-600'
                            ]" />
                    </div>
                </div>

                <div class="flex justify-end items-center pt-3 mt-auto space-x-1">
                    <template v-if="rule.isEditing">
                        <button @click="saveEditedRule(rule)"
                            class="p-2 text-slate-600 rounded-full hover:bg-green-100 hover:text-green-600 focus:outline-none focus:ring-2 focus:ring-green-500">
                            <font-awesome-icon :icon="['fas', 'check']" class="h-4 w-4" />
                        </button>
                        <button @click="cancelEditing(index)"
                            class="p-2 text-slate-600 rounded-full hover:bg-slate-200 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500">
                            <font-awesome-icon :icon="['fas', 'xmark']" class="h-4 w-4" />
                        </button>
                    </template>
                    <template v-else>
                        <button @click="startEditing(rule, index)"
                            class="p-2 text-slate-500 rounded-full hover:bg-slate-200 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500">
                            <font-awesome-icon :icon="['fas', 'pen']" class="h-4 w-4" />
                        </button>
                        <button @click="removeRule(index)"
                            class="p-2 text-slate-500 rounded-full hover:bg-red-100 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500">
                            <font-awesome-icon :icon="['fas', 'trash']" class="h-4 w-4" />
                        </button>
                    </template>
                </div>
            </div>
        </div>

        <p v-if="rules.length === 0" class="text-gray-500 text-center py-8">No fine-tuning rules defined yet.</p>

    </div>

    <Transition name="fade">
        <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60"
            @click="closeModal">
            <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 sm:p-8 m-4" @click.stop>
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-xl font-bold text-gray-800">Add New Rule</h3>
                    <button @click="closeModal"
                        class="p-2 text-slate-500 rounded-full hover:bg-slate-200 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500">
                        <font-awesome-icon :icon="['fas', 'xmark']" class="h-5 w-5" />
                    </button>
                </div>
                <form @submit.prevent="addRule" class="space-y-4">
                    <div>
                        <label for="new-trigger" class="block text-sm font-medium text-gray-700 mb-1">Trigger</label>
                        <input v-model="newRule.trigger" type="text" id="new-trigger" placeholder="e.g., 'summarize:'"
                            class="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400" />
                    </div>
                    <div>
                        <label for="new-instruction"
                            class="block text-sm font-medium text-gray-700 mb-1">Instruction</label>
                        <AutoGrowTextarea v-model="newRule.instruction" id="new-instruction" rows="3"
                            placeholder="e.g., 'Summarize the following text concisely.'"
                            class="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400" />
                    </div>
                    <div class="flex justify-end pt-4 space-x-3">
                        <button type="button" @click="closeModal"
                            class="px-4 py-2 rounded-lg font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400">
                            Cancel
                        </button>
                        <button type="submit"
                            class="px-4 py-2 rounded-lg font-semibold text-white bg-purple-500 hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                            Add Rule
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import { useToast } from '../../composables/useToast'
import AutoGrowTextarea from '../AutoGrowTextarea.vue'

const tenantsStore = useTenantsStore()
const { addToast } = useToast()

const isModalOpen = ref(false)
const rules = ref([])
const newRule = ref({ trigger: '', instruction: '' })

// A temporary store for the rule's state before editing, in case of cancellation
let originalRuleState = null

watch(() => tenantsStore.currentTenant, (newTenant) => {
    if (newTenant && newTenant.tenant_fine_tune) {
        // Add the isEditing flag to each rule when loading
        rules.value = JSON.parse(JSON.stringify(newTenant.tenant_fine_tune)).map(rule => ({
            ...rule,
            isEditing: false
        }));
    } else {
        rules.value = []
    }
}, { immediate: true, deep: true })


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
    isModalOpen.value = false
    newRule.value = { trigger: '', instruction: '' }
}

// A generic function to save the current state of rules to the backend
const saveRules = async () => {
    if (tenantsStore.currentTenant) {
        // Create a "clean" version of rules without the isEditing flag for the backend
        const rulesToSave = rules.value.map(({ isEditing, ...rest }) => rest);
        const updateData = { fine_tune_rules: rulesToSave }
        try {
            await tenantsStore.updateTenant(tenantsStore.currentTenant.id, updateData)
            addToast('Fine-tuning rules saved successfully!', 'success')
            return true // Indicate success
        } catch (error) {
            addToast('Failed to save fine-tuning rules.', 'error')
            return false // Indicate failure
        }
    }
    return false
}

const addRule = async () => {
    if (newRule.value.trigger.trim() && newRule.value.instruction.trim()) {
        rules.value.push({ ...newRule.value, isEditing: false })
        const success = await saveRules()
        if (success) {
            closeModal()
        } else {
            rules.value.pop()
        }
    }
}

const removeRule = async (index) => {
    const ruleBackup = rules.value[index]
    rules.value.splice(index, 1)
    const success = await saveRules()
    if (!success) {
        rules.value.splice(index, 0, ruleBackup)
    }
}
</script>