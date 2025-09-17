<template>
  <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
    <h3 class="text-xl font-bold text-brand-white mb-4">Fine-Tuning Rules</h3>

    <!-- Form to add new rule -->
    <form @submit.prevent="addRule" class="mb-6 flex items-start space-x-4">
      <div class="flex-grow">
        <label for="trigger" class="block text-sm font-medium text-gray-300">Trigger</label>
        <input v-model="newRule.trigger" type="text" id="trigger" placeholder="e.g., Questions about pricing"
          class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg" />
      </div>
      <div class="flex-grow">
        <label for="instruction" class="block text-sm font-medium text-gray-300">Instruction</label>
        <textarea v-model="newRule.instruction" id="instruction" rows="2" placeholder="e.g., Always refer to the pricing page..."
          class="w-full p-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-lg"></textarea>
      </div>
      <button type="submit" class="self-end mb-1 bg-black border border-white hover:bg-gray-900 text-white font-bold py-2 px-4 rounded-lg">Add Rule</button>
    </form>

    <!-- List of existing rules -->
    <div class="space-y-4">
      <div v-for="(rule, index) in rules" :key="index" class="bg-gray-700 p-4 rounded-lg">
        <div class="flex justify-between items-start">
          <div>
            <p class="font-semibold text-gray-300">Trigger:</p>
            <p class="mb-2">{{ rule.trigger }}</p>
            <p class="font-semibold text-gray-300">Instruction:</p>
            <p>{{ rule.instruction }}</p>
          </div>
          <button @click="removeRule(index)" class="text-red-500 hover:text-red-400">&times;</button>
        </div>
      </div>
       <p v-if="rules.length === 0" class="text-gray-500">No fine-tuning rules defined yet.</p>
    </div>

    <!-- Save Changes Button -->
    <div class="flex justify-end mt-6">
       <button @click="handleUpdate" :disabled="tenantsStore.loading"
          class="bg-black border border-white hover:bg-gray-900 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50">
          {{ tenantsStore.loading ? 'Saving...' : 'Save All Rules' }}
        </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTenantsStore } from '../../stores/tenants'

const tenantsStore = useTenantsStore()
const rules = ref([])
const newRule = ref({ trigger: '', instruction: '' })

watch(() => tenantsStore.currentTenant, (newTenant) => {
  if (newTenant && newTenant.tenant_fine_tune) {
    // Create a deep copy to avoid direct mutation of the store's state
    rules.value = JSON.parse(JSON.stringify(newTenant.tenant_fine_tune))
  }
}, { immediate: true, deep: true })

const addRule = () => {
  if (newRule.value.trigger.trim() && newRule.value.instruction.trim()) {
    rules.value.push({ ...newRule.value })
    newRule.value = { trigger: '', instruction: '' } // Reset form
  }
}

const removeRule = (index) => {
  rules.value.splice(index, 1)
}

const handleUpdate = async () => {
  if (tenantsStore.currentTenant) {
    // We only need to pass the fine_tune_rules in the payload
    const updateData = { fine_tune_rules: rules.value }
    await tenantsStore.updateTenant(tenantsStore.currentTenant.id, updateData)
  }
}
</script>
