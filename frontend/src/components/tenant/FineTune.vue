<template>
    <div class="card">
        <h3 class="text-xl font-bold text-base-content mb-4 flex items-center">
            <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" class="mr-3 text-primary" />
            Fine-Tuning Rules
        </h3>

        <!-- Form to add new rule -->
        <form @submit.prevent="addRule"
            class="mb-6 flex flex-col sm:flex-row items-start sm:space-x-4 space-y-4 sm:space-y-0">
            <div class="flex-grow w-full">
                <label for="trigger" class="block text-sm font-medium text-base-content">Trigger</label>
                <input v-model="newRule.trigger" type="text" id="trigger" placeholder="e.g., Questions about pricing"
                    class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div class="flex-grow w-full">
                <label for="instruction" class="block text-sm font-medium text-base-content">Instruction</label>
                <textarea v-model="newRule.instruction" ref="newInstructionTextarea" id="instruction" rows="1"
                    placeholder="e.g., Always refer to the pricing page..."
                    class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none overflow-hidden"></textarea>
            </div>
            <button type="submit" class="self-end sm:self-end mb-1 btn btn-primary">
                <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
                Add Rule
            </button>
        </form>

        <!-- List of existing rules -->
        <div class="space-y-4">
            <div v-for="(rule, index) in rules" :key="index" class="bg-base-200 p-4 rounded-lg">
                <div class="flex justify-between items-start space-x-4">
                    <div class="flex-grow space-y-2">
                        <div>
                            <label :for="`trigger-${index}`"
                                class="block text-sm font-medium text-base-content">Trigger</label>
                            <input v-model="rule.trigger" type="text" :id="`trigger-${index}`"
                                class="w-full p-2 mt-1 bg-base-300 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                        </div>
                        <div>
                            <label :for="`instruction-${index}`"
                                class="block text-sm font-medium text-base-content">Instruction</label>
                            <textarea v-model="rule.instruction" :ref="el => instructionTextareas[index] = el"
                                :id="`instruction-${index}`" rows="1"
                                class="w-full p-2 mt-1 bg-base-300 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none overflow-hidden"></textarea>
                        </div>
                    </div>
                    <button @click="removeRule(index)" class="btn btn-sm text-error hover:bg-error/10 self-center">
                        <font-awesome-icon :icon="['fas', 'trash']" />
                    </button>
                </div>
            </div>
            <p v-if="rules.length === 0" class="text-base-content/70">No fine-tuning rules defined yet.</p>
        </div>

        <!-- Save Changes Button -->
        <div class="flex justify-end mt-6">
            <button @click="handleUpdate" :disabled="tenantsStore.loading" class="btn btn-primary">
                <span v-if="tenantsStore.loading" class="flex items-center justify-center">
                    <font-awesome-icon :icon="['fas', 'spinner']" class="w-5 h-5 mr-3 animate-spin" />
                    Saving...
                </span>
                <span v-else class="flex items-center">
                    <font-awesome-icon :icon="['fas', 'save']" class="mr-2" />
                    Save All Rules
                </span>
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import { useToast } from '../../composables/useToast'

const tenantsStore = useTenantsStore()
const { addToast } = useToast()
const rules = ref([])
const newRule = ref({ trigger: '', instruction: '' })

const newInstructionTextarea = ref(null)
const instructionTextareas = ref([])

const autosizeTextarea = (textarea) => {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
};

// Watch for changes in the new rule's instruction and autosize
watch(() => newRule.value.instruction, () => {
    nextTick(() => autosizeTextarea(newInstructionTextarea.value));
});

// Watch for changes in the list of rules and autosize all textareas
watch(rules, () => {
    nextTick(() => {
        instructionTextareas.value.forEach(autosizeTextarea);
    });
}, { deep: true, immediate: true });


watch(() => tenantsStore.currentTenant, (newTenant) => {
    if (newTenant && newTenant.tenant_fine_tune) {
        rules.value = JSON.parse(JSON.stringify(newTenant.tenant_fine_tune))
    } else {
        rules.value = []
    }
    nextTick(() => {
        instructionTextareas.value.forEach(autosizeTextarea);
    });
}, { immediate: true, deep: true })

const addRule = () => {
    if (newRule.value.trigger.trim() && newRule.value.instruction.trim()) {
        rules.value.push({ ...newRule.value })
        newRule.value = { trigger: '', instruction: '' } // Reset form
        nextTick(() => {
            if (newInstructionTextarea.value) {
                newInstructionTextarea.value.style.height = 'auto';
            }
        });
    }
}

const removeRule = (index) => {
    rules.value.splice(index, 1)
}

const handleUpdate = async () => {
    if (tenantsStore.currentTenant) {
        const updateData = { fine_tune_rules: rules.value }
        try {
            await tenantsStore.updateTenant(tenantsStore.currentTenant.id, updateData)
            addToast('Fine-tuning rules saved successfully!', 'success')
        } catch (error) {
            addToast('Failed to save fine-tuning rules.', 'error')
        }
    }
}
</script>
