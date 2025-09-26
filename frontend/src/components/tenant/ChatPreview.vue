<template>
    <div class="rounded-2xl shadow-lg overflow-hidden border border-base-300" :style="widgetCssVariables">

        <header class="p-3 flex justify-between items-center"
            style="background-color: var(--chat-header-background-color); color: var(--chat-header-text-color);">
            <div class="w-1/4"></div>
            <h1 class="text-md font-bold text-center w-1/2 flex items-center justify-center">
                <img v-if="config.logo" :src="config.logo" class="h-6 mr-2" />
                <span>{{ config.chatbot_title }}</span>
            </h1>
            <div class="w-1/4 flex justify-end">
                <button v-if="config.show_reset_button" class="btn btn-secondary btn-xs btn-square rounded-full aspect-square">
                    <font-awesome-icon :icon="['fas', 'arrows-rotate']" />
                </button>
            </div>
        </header>

        <main class="p-4 text-sm" style="background-color: var(--chat-background-color); height: 400px;">
            <div class="flex justify-start mb-3">
                <div class="max-w-xl lg:max-w-2xl px-5 py-3 shadow-md" :style="botMessageStyle">
                    Welcome! How can I help you today?
                </div>
            </div>
            <div class="flex justify-end mb-3">
                <div class="max-w-xl lg:max-w-2xl px-5 py-3 shadow-md" :style="userMessageStyle">
                    Tell me about your services.
                </div>
            </div>
            <div class="flex justify-start">
                <div class="max-w-xl lg:max-w-2xl px-5 py-3 shadow-md flex items-center space-x-2"
                    :style="botMessageStyle">
                    <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce"></span>
                    <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce"
                        style="animation-delay: 150ms;"></span>
                    <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce"
                        style="animation-delay: 300ms;"></span>
                </div>
            </div>
        </main>

        <footer class="p-3" style="background-color: var(--chat-header-background-color);">
            <div class="flex gap-1">
                <input type="text" placeholder="Ask a question..."
                    class="chat-input flex-grow border px-5 py-3 text-sm focus:outline-none focus:ring-2 rounded-full"
                    :style="chatInputStyle">
                <button class="send-button font-bold py-2 px-4 btn-secondary btn-square rounded-full aspect-square"
                    :style="sendButtonStyle">
                    <font-awesome-icon :icon="['fas', 'paper-plane']" />
                </button>
            </div>
        </footer>
    </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
    config: {
        type: Object,
        required: true
    }
});

const widgetCssVariables = computed(() => {
    const config = props.config;
    if (!config) return {};

    const styles = config.component_styles || {};
    const palette = config.color_palette || [];
    const findColor = (colorId, fallback = '#000000') => palette.find(c => c.id === colorId)?.value || fallback;

    return {
        '--chat-header-background-color': findColor(styles.header_background_color, '#F3F4F6'),
        '--chat-header-text-color': findColor(styles.header_text_color, '#1F2937'),
        '--chat-user-message-background-color': findColor(styles.user_message_background_color, '#A855F7'),
        '--chat-user-message-text-color': findColor(styles.user_message_text_color, '#FFFFFF'),
        '--chat-bot-message-background-color': findColor(styles.bot_message_background_color, '#F3F4F6'),
        '--chat-bot-message-text-color': findColor(styles.bot_message_text_color, '#1F2937'),
        '--chat-send-button-background-color': findColor(styles.send_button_background_color, '#A855F7'),
        '--chat-send-button-text-color': findColor(styles.send_button_text_color, '#FFFFFF'),
        '--chat-input-background-color': findColor(styles.input_background_color, '#F9FAFB'),
        '--chat-input-text-color': findColor(styles.input_text_color, '#1F2937'),
        '--chat-input-focus-ring-color': findColor(styles.input_focus_ring_color, '#A855F7'),
        '--chat-background-color': findColor(styles.chat_background_color, '#FFFFFF'),
        '--chat-border-radius': '24px', // Synced from main chat
    };
});

const userMessageStyle = computed(() => ({
    backgroundColor: 'var(--chat-user-message-background-color)',
    color: 'var(--chat-user-message-text-color)',
    borderRadius: 'var(--chat-border-radius)',
}));

const botMessageStyle = computed(() => ({
    backgroundColor: 'var(--chat-bot-message-background-color)',
    color: 'var(--chat-bot-message-text-color)',
    borderRadius: 'var(--chat-border-radius)',
}));


const chatInputStyle = computed(() => ({
    backgroundColor: 'var(--chat-input-background-color)',
    color: 'var(--chat-input-text-color)',
    borderColor: 'var(--chat-header-background-color)',
    '--tw-ring-color': 'var(--chat-input-focus-ring-color)'
}));

const sendButtonStyle = computed(() => ({
    backgroundColor: 'var(--chat-send-button-background-color)',
    color: 'var(--chat-send-button-text-color)',
}));
</script>

<style scoped>
.chat-input::placeholder {
    color: var(--chat-input-text-color);
    opacity: 0.8;
}
</style>