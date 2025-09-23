<template>
    <div class="card">
        <form @submit.prevent="handleUpdate" class="space-y-6">
            <div>
                <label for="name" class="block text-sm font-medium text-base-content">Tenant Name</label>
                <input v-model="formData.name" type="text" id="name" required
                    class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
                <label for="intro_message" class="block text-sm font-medium text-base-content">Intro Message</label>
                <AutoGrowTextarea v-model="formData.intro_message" id="intro_message" rows="3"
                    class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
                <label for="system_persona" class="block text-sm font-medium text-base-content">System Persona</label>
                <AutoGrowTextarea v-model="formData.system_persona" id="system_persona" rows="5"
                    class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
                <label for="rag_prompt_template" class="block text-sm font-medium text-base-content">RAG Prompt
                    Template</label>
                <AutoGrowTextarea v-model="formData.rag_prompt_template" id="rag_prompt_template" rows="8"
                    class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label for="doc_language" class="block text-sm font-medium text-base-content">Document
                        Language</label>
                    <input v-model="formData.doc_language" type="text" id="doc_language"
                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
                <div>
                    <label for="translation_target" class="block text-sm font-medium text-base-content">Translation
                        Target</label>
                    <input v-model="formData.translation_target" type="text" id="translation_target"
                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
            </div>
            <div>
                <label for="doc_description" class="block text-sm font-medium text-base-content">Document
                    Description</label>
                <input v-model="formData.doc_description" type="text" id="doc_description"
                    class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
                <label for="source_description" class="block text-sm font-medium text-base-content">Source
                    Description</label>
                <input v-model="formData.source_description" type="text" id="source_description"
                    class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
                <label for="last_updated_description" class="block text-sm font-medium text-base-content">Last Updated
                    Description</label>
                <input v-model="formData.last_updated_description" type="text" id="last_updated_description"
                    class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div class="flex justify-end">
                <button type="submit" :disabled="tenantsStore.loading" class="btn btn-primary">
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
        </form>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import { useToast } from '../../composables/useToast'
import AutoGrowTextarea from '../AutoGrowTextarea.vue'

const tenantsStore = useTenantsStore()
const { addToast } = useToast()
const formData = ref({
    name: '',
    intro_message: '',
    system_persona: '',
    rag_prompt_template: '',
    doc_language: '',
    doc_description: '',
    source_description: '',
    last_updated_description: '',
    translation_target: '',
})

watch(() => tenantsStore.currentTenant, (newTenant) => {
    if (newTenant) {
        formData.value = {
            name: newTenant.name,
            intro_message: newTenant.intro_message,
            system_persona: newTenant.system_persona,
            rag_prompt_template: newTenant.rag_prompt_template,
            doc_language: newTenant.doc_language,
            doc_description: newTenant.doc_description,
            source_description: newTenant.source_description,
            last_updated_description: newTenant.last_updated_description,
            translation_target: newTenant.translation_target,
        }
    }
}, { immediate: true, deep: true })

const handleUpdate = async () => {
    if (tenantsStore.currentTenant) {
        try {
            await tenantsStore.updateTenant(tenantsStore.currentTenant.id, formData.value)
            addToast('Settings saved successfully!', 'success')
        } catch (error) {
            addToast('Failed to save settings.', 'error')
        }
    }
}
</script>
