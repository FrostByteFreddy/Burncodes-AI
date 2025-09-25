<template>
    <div class="card">
        <div class="tabs tabs-boxed bg-base-200">
            <a class="tab" :class="{ 'tab-active': activeTab === 'general' }" @click="activeTab = 'general'">General</a>
            <a class="tab" :class="{ 'tab-active': activeTab === 'widget' }" @click="activeTab = 'widget'">Widget</a>
        </div>

        <form @submit.prevent="handleUpdate" class="space-y-6 mt-6">
            <div v-show="activeTab === 'general'">
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
                        <select v-model="formData.doc_language" id="doc_language"
                            class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary">
                            <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">
                                {{ lang.text }}
                            </option>
                        </select>
                    </div>
                    <div>
                        <label for="translation_target" class="block text-sm font-medium text-base-content">Translation
                            Target</label>
                        <select v-model="formData.translation_target" id="translation_target"
                            class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary">
                            <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">
                                {{ lang.text }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>

            <div v-show="activeTab === 'widget'" class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label for="primary_color" class="block text-sm font-medium text-base-content">Primary
                            Color</label>
                        <input v-model="formData.widget_config.primary_color" type="color" id="primary_color"
                            class="w-full h-12 p-1 mt-1 bg-base-200 border border-base-300 rounded-lg cursor-pointer" />
                    </div>
                    <div>
                        <label for="secondary_color" class="block text-sm font-medium text-base-content">Secondary
                            Color</label>
                        <input v-model="formData.widget_config.secondary_color" type="color" id="secondary_color"
                            class="w-full h-12 p-1 mt-1 bg-base-200 border border-base-300 rounded-lg cursor-pointer" />
                    </div>
                </div>
                <div>
                    <label for="chatbot_logo" class="block text-sm font-medium text-base-content">Chatbot Logo</label>
                    <input @change="handleFileUpload($event, 'chatbot_logo')" type="file" id="chatbot_logo"
                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg" accept="image/*" />
                    <img v-if="formData.widget_config.chatbot_logo" :src="formData.widget_config.chatbot_logo"
                        class="mt-4 max-h-20" />
                </div>
                <div>
                    <label for="widget_icon" class="block text-sm font-medium text-base-content">Widget Icon</label>
                    <input @change="handleFileUpload($event, 'widget_icon')" type="file" id="widget_icon"
                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg" accept="image/*" />
                    <img v-if="formData.widget_config.widget_icon" :src="formData.widget_config.widget_icon"
                        class="mt-4 max-h-20" />
                </div>
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
const activeTab = ref('general')

const languageOptions = ref([
    { value: 'de', text: 'German' },
    { value: 'en', text: 'English' },
    { value: 'fr', text: 'French' }
])

const formData = ref({
    name: '',
    intro_message: '',
    system_persona: '',
    rag_prompt_template: '',
    doc_language: 'en',
    doc_description: '',
    source_description: '',
    last_updated_description: '',
    translation_target: 'en',
    widget_config: {
        primary_color: '#000000',
        secondary_color: '#FFFFFF',
        chatbot_logo: null,
        widget_icon: null,
    }
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
            widget_config: newTenant.widget_config || {
                primary_color: '#000000',
                secondary_color: '#FFFFFF',
                chatbot_logo: null,
                widget_icon: null,
            }
        }
    }
}, { immediate: true, deep: true })

const handleFileUpload = (event, field) => {
    const file = event.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
        formData.value.widget_config[field] = e.target.result
    }
    reader.readAsDataURL(file)
}

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
