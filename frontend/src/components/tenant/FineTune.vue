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

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="(rule, index) in rules" :key="index"
                class="group bg-primary-light p-4 rounded-xl border border-gray-200 flex flex-col transition-all duration-300 hover:shadow-md">
                <div class="flex-grow space-y-3">
                    <div>
                        <label :for="`trigger-${index}`"
                            class="block text-sm font-medium text-gray-700">Trigger</label>
                        <input v-model="rule.trigger" type="text" :id="`trigger-${index}`"
                            class="w-full p-2 mt-1 border text-white bg-primary-light border-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                    </div>
                    <div>
                        <label :for="`instruction-${index}`"
                            class="block text-sm font-medium text-gray-700">Instruction</label>
                        <AutoGrowTextarea v-model="rule.instruction" :id="`instruction-${index}`" rows="1"
                            class="w-full p-2 mt-1 border text-white bg-primary-light border-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                    </div>
                </div>

                <div class="flex justify-end pt-3 mt-auto">
                    <button @click="removeRule(index)"
                        class="p-2 text-gray-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 hover:bg-red-100 hover:text-red-500 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-500">
                        <font-awesome-icon :icon="['fas', 'trash']" class="h-4 w-4" />
                    </button>
                </div>
            </div>
        </div>

        <p v-if="rules.length === 0" class="text-gray-500 text-center py-8">No fine-tuning rules defined yet.</p>

        <div v-if="hasChanges" class="flex justify-end mt-6">
            <button @click="saveRules" :disabled="tenantsStore.loading"
                class="inline-flex items-center px-4 py-2 font-semibold text-white bg-purple-500 rounded-lg shadow-sm hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed">
                <span v-if="tenantsStore.loading" class="flex items-center justify-center">
                    <font-awesome-icon :icon="['fas', 'spinner']" class="w-5 h-5 mr-3 animate-spin" />
                    Saving...
                </span>
                <span v-else class="flex items-center">
                    <font-awesome-icon :icon="['fas', 'save']" class="mr-2" />
                    Save Changes
                </span>
            </button>
        </div>
    </div>

    <Transition name="fade">
        <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60"
            @click.self="closeModal">
            <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 mx-4" role="dialog" aria-modal="true">
                <h4 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
                    <font-awesome-icon :icon="['fas', 'plus-circle']" class="mr-3 text-purple-500" />
                    Add a New Rule
                </h4>
                <form @submit.prevent="addRule" class="space-y-4">
                    <div class="flex-grow w-full">
                        <label for="trigger" class="block text-sm font-medium text-gray-700">Trigger</label>
                        <input v-model="newRule.trigger" type="text" id="trigger"
                            placeholder="e.g., Questions about pricing"
                            class="w-full p-2 mt-1 bg-gray-100 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                    <div class="flex-grow w-full">
                        <label for="instruction" class="block text-sm font-medium text-gray-700">Instruction</label>
                        <AutoGrowTextarea v-model="newRule.instruction" id="instruction" rows="3"
                            placeholder="e.g., Always refer to the pricing page..."
                            class="w-full p-2 mt-1 bg-gray-100 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                    <div class="flex justify-end space-x-3 pt-2">
                        <button type="button" @click="closeModal"
                            class="px-4 py-2 font-semibold text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400">
                            Cancel
                        </button>
                        <button type="submit"
                            class="inline-flex items-center px-4 py-2 font-semibold text-white bg-purple-500 rounded-lg shadow-sm hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                            <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
                            Add and Save Rule
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </Transition>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import { useToast } from '../../composables/useToast'
import AutoGrowTextarea from '../AutoGrowTextarea.vue'

const tenantsStore = useTenantsStore()
const { addToast } = useToast()

// State for modal visibility
const isModalOpen = ref(false)
const rules = ref([])
const newRule = ref({ trigger: '', instruction: '' })

// A pristine copy of the rules to detect if any edits have been made
const originalRules = ref([])

// Computed property to check for changes by comparing the current rules to the original state
const hasChanges = computed(() => {
    return JSON.stringify(rules.value) !== JSON.stringify(originalRules.value)
})

watch(() => tenantsStore.currentTenant, (newTenant) => {
    if (newTenant && newTenant.tenant_fine_tune) {
        const loadedRules = JSON.parse(JSON.stringify(newTenant.tenant_fine_tune))
        rules.value = loadedRules
        originalRules.value = JSON.parse(JSON.stringify(loadedRules)) // Set initial state for comparison
    } else {
        rules.value = []
        originalRules.value = []
    }
}, { immediate: true, deep: true })

const closeModal = () => {
    isModalOpen.value = false
    // Reset form when closing
    newRule.value = { trigger: '', instruction: '' }
}

// A generic function to save the current state of rules to the backend
const saveRules = async () => {
    if (tenantsStore.currentTenant) {
        const updateData = { fine_tune_rules: rules.value }
        try {
            await tenantsStore.updateTenant(tenantsStore.currentTenant.id, updateData)
            addToast('Fine-tuning rules saved successfully!', 'success')
            // After a successful save, update the original state to the current state
            originalRules.value = JSON.parse(JSON.stringify(rules.value))
            return true // Indicate success
        } catch (error) {
            addToast('Failed to save fine-tuning rules.', 'error')
            return false // Indicate failure
        }
    }
    return false
}


// Adds a new rule, saves it, and closes the modal
const addRule = async () => {
    if (newRule.value.trigger.trim() && newRule.value.instruction.trim()) {
        rules.value.push({ ...newRule.value })
        const success = await saveRules()
        if (success) {
            closeModal() // Close modal on success
        } else {
            // If save failed, remove the optimistically added rule
            rules.value.pop()
        }
    }
}

// Removes a rule and saves the change immediately
const removeRule = async (index) => {
    const ruleBackup = rules.value[index]
    rules.value.splice(index, 1)
    const success = await saveRules()
    if (!success) {
        // If save failed, restore the rule to the list
        rules.value.splice(index, 0, ruleBackup)
    }
}
</script>