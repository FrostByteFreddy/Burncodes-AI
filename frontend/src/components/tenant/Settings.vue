<template>
    <div class="card">
        <div class="inline-flex p-1 space-x-1 bg-primary-light rounded-full">
            <a class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
                :class="{ '!bg-primary-focus text-primary-content shadow': activeTab === 'behavior', 'btn-ghost text-base-content': activeTab !== 'behavior' }"
                @click="activeTab = 'behavior'">
                <font-awesome-icon :icon="['fas', 'fa-brain']" />
                <span>Behavior</span>
            </a>
            <a class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
                :class="{ '!bg-primary-focus text-primary-content shadow': activeTab === 'appearance', 'btn-ghost text-base-content': activeTab !== 'appearance' }"
                @click="activeTab = 'appearance'">
                <font-awesome-icon :icon="['fas', 'fa-palette']" />
                <span>Appearance</span>
            </a>
        </div>

        <form @submit.prevent="handleUpdate" class="space-y-6 mt-6">
            <div v-show="activeTab === 'behavior'" class="space-y-6">
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
                    <label for="system_persona" class="block text-sm font-medium text-base-content">System
                        Persona</label>
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

            <div v-show="activeTab === 'appearance'" @change="handleUpdate">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">

                    <div class="space-y-8">
                        <div class="p-4 border border-base-300 rounded-lg">
                            <h3 class="text-lg font-bold mb-4">Branding & General</h3>
                            <div class="space-y-4">
                                <div>
                                    <label for="chatbot_title" class="block text-sm font-medium">Chatbot Title</label>
                                    <input v-model="formData.widget_config.chatbot_title" type="text" id="chatbot_title"
                                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                                </div>
                                <div>
                                    <label for="logo" class="block text-sm font-medium">Logo</label>
                                    <input @change="handleFileUpload($event, 'logo')" type="file" id="logo"
                                        class="w-full p-2 mt-1 bg-base-200 border border-base-300 rounded-lg file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                                        accept="image/*" />
                                    <img v-if="formData.widget_config.logo" :src="formData.widget_config.logo"
                                        class="mt-4 max-h-20 rounded-md" />
                                </div>
                                <div class="flex items-center">
                                    <input v-model="formData.widget_config.show_reset_button" type="checkbox"
                                        id="show_reset_button"
                                        class="h-4 w-4 rounded border-base-300 text-primary focus:ring-primary" />
                                    <label for="show_reset_button" class="ml-2 block text-sm">Show "Reset Chat"
                                        Button</label>
                                </div>
                                <div>
                                    <label for="input_placeholder" class="block text-sm font-medium">Input
                                        Placeholder</label>
                                    <input v-model="formData.widget_config.input_placeholder" type="text"
                                        id="input_placeholder"
                                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" />
                                </div>
                                <div>
                                    <label for="thinking_messages" class="block text-sm font-medium">"Thinking"
                                        Messages</label>
                                    <AutoGrowTextarea v-model="thinkingMessages" id="thinking_messages"
                                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                        rows="3" placeholder="One message per line..." /></div>
                            </div>
                        </div>

                        <div class="p-4 border border-base-300 rounded-lg">
                            <h3 class="text-lg font-bold mb-4">Color Palette</h3>
                            <p class="text-sm text-base-content/70 mb-4">Define your brand colors here. You can then
                                assign these
                                colors to different parts of the chat widget below.</p>
                            <div class="space-y-3">
                                <div v-for="(color, index) in formData.widget_config.color_palette" :key="color.id"
                                    class="flex items-center space-x-3">
                                    <input v-model="color.value" type="color"
                                        class="w-12 h-10 p-1 bg-base-200 border-none rounded-lg cursor-pointer aspect-square" />
                                    <input v-model="color.name" type="text"
                                        placeholder="Color Name (e.g., Brand Purple)" :disabled="index < 2"
                                        class="flex-grow p-2 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-base-300/50" />
                                    <button @click.prevent="removeColor(color.id)" v-if="index > 1"
                                        class="btn btn-ghost btn-sm text-error">
                                        <font-awesome-icon :icon="['fas', 'trash']" />
                                    </button>
                                </div>
                            </div>
                            <button @click.prevent="addColor" class="btn btn-secondary btn-sm mt-4">
                                <font-awesome-icon :icon="['fas', 'plus']" class="mr-2" />
                                Add Color
                            </button>
                        </div>

                        <div class="p-4 border border-base-300 rounded-lg">
                            <h3 class="text-lg font-bold mb-4">Component Styles</h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                                <div v-for="(label, key) in componentStyleLabels" :key="key">
                                    <label :for="key" class="block text-sm font-medium">{{ label }}</label>
                                    <select v-model="formData.widget_config.component_styles[key]" :id="key"
                                        class="w-full p-3 mt-1 bg-base-200 border border-base-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary">
                                        <option v-for="color in formData.widget_config.color_palette" :key="color.id"
                                            :value="color.id">
                                            {{ color.name }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div class="lg:sticky top-8">
                            <h3 class="text-lg font-bold mb-4">Live Preview</h3>
                            <ChatPreview :tenantId="tenantsStore.currentTenant.id" :key="previewKey" />
                        </div>
                    </div>
                </div>
            </div>

            <div class="flex justify-end mt-8">
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
import { ref, watch, computed } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import { useToast } from '../../composables/useToast'
import AutoGrowTextarea from '../AutoGrowTextarea.vue'
import { v4 as uuidv4 } from 'uuid'
import ChatPreview from './ChatPreview.vue'

const tenantsStore = useTenantsStore()
const { addToast } = useToast()
const activeTab = ref('behavior')
const previewKey = ref(0)

const languageOptions = ref([
    { value: 'de', text: 'German' },
    { value: 'en', text: 'English' },
    { value: 'fr', text: 'French' }
])

const defaultWidgetConfig = () => ({
    chatbot_title: '',
    logo: null,
    show_reset_button: true,
    input_placeholder: 'Send a message...',
    thinking_messages: ['Thinking...', 'Just a moment...', 'Let me check that for you...'],
    color_palette: [
        { id: 'c_white', name: 'White', value: '#FFFFFF' },
        { id: 'c_black', name: 'Black', value: '#1F2937' },
        { id: 'c_primary', name: 'Primary', value: '#A855F7' },
        { id: 'c_secondary', name: 'Secondary', value: '#F3F4F6' },
    ],
    component_styles: {
        header_background_color: 'c_secondary',
        header_text_color: 'c_black',
        user_message_background_color: 'c_primary',
        user_message_text_color: 'c_white',
        bot_message_background_color: 'c_secondary',
        bot_message_text_color: 'c_black',
        send_button_background_color: 'c_primary',
        send_button_text_color: 'c_white',
        input_background_color: 'c_secondary',
        input_text_color: 'c_black',
        input_focus_ring_color: 'c_primary',
        chat_background_color: 'c_white',
        reset_button_color: 'c_primary',
    }
});

const formData = ref({
    name: '',
    intro_message: '',
    system_persona: '',
    rag_prompt_template: '',
    doc_language: 'en',
    translation_target: 'en',
    widget_config: defaultWidgetConfig()
})

const componentStyleLabels = {
    header_background_color: 'Header Background',
    header_text_color: 'Header Text',
    user_message_background_color: 'User Message Background',
    user_message_text_color: 'User Message Text',
    bot_message_background_color: 'Bot Message Background',
    bot_message_text_color: 'Bot Message Text',
    send_button_background_color: 'Send Button Background',
    send_button_text_color: 'Send Button Text',
    input_background_color: 'Input Field Background',
    input_text_color: 'Input Field Text',
    input_focus_ring_color: 'Input Field Focus Ring',
    chat_background_color: 'Chat Area Background',
    reset_button_color: 'Reset Button',
};

watch(() => tenantsStore.currentTenant, (newTenant) => {
    if (newTenant) {
        // Deep merge the tenant's config with the default to prevent errors if the structure is old
        const newConfig = {
            ...defaultWidgetConfig(),
            ...(newTenant.widget_config || {})
        };
        newConfig.color_palette = newTenant.widget_config?.color_palette || defaultWidgetConfig().color_palette;
        newConfig.component_styles = {
            ...defaultWidgetConfig().component_styles,
            ...(newTenant.widget_config?.component_styles || {})
        };

        formData.value = {
            name: newTenant.name,
            intro_message: newTenant.intro_message,
            system_persona: newTenant.system_persona,
            rag_prompt_template: newTenant.rag_prompt_template,
            doc_language: newTenant.doc_language,
            translation_target: newTenant.translation_target,
            widget_config: newConfig
        }
    }
}, { immediate: true, deep: true })

const thinkingMessages = computed({
    get: () => formData.value.widget_config.thinking_messages.join('\n'),
    set: (value) => {
        formData.value.widget_config.thinking_messages = value.split('\n').map(s => s.trim()).filter(Boolean);
    }
});

const addColor = () => {
    formData.value.widget_config.color_palette.push({
        id: uuidv4(),
        name: 'New Color',
        value: '#000000'
    })
}

const removeColor = (idToRemove) => {
    const palette = formData.value.widget_config.color_palette
    if (palette.length <= 2) {
        addToast('Cannot remove base colors.', 'warning')
        return
    }
    formData.value.widget_config.color_palette = palette.filter(c => c.id !== idToRemove)
}

// Encodes a file as a base64 string
const encodeFileAsBase64 = (file) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = (error) => reject(error);
        reader.readAsDataURL(file);
    });
};

const handleFileUpload = async (event, field) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const base64String = await encodeFileAsBase64(file);
        formData.value.widget_config[field] = base64String;
        addToast('Logo preview updated!', 'success');
    } catch (error) {
        console.error('File reading error:', error);
        addToast('Failed to read file. Please try a different image.', 'error');
    }
};

const handleUpdate = async () => {
    if (tenantsStore.currentTenant && !tenantsStore.loading) {
        try {
            await tenantsStore.updateTenant(tenantsStore.currentTenant.id, formData.value)
            addToast('Settings saved successfully!', 'success')
            previewKey.value++
        } catch (error) {
            addToast('Failed to save settings.', 'error')
        }
    }
}
</script>