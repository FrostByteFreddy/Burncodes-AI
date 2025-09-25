<template>
    <div class="rounded-2xl shadow-lg overflow-hidden border border-base-300" :style="widgetCssVariables">

        <header class="p-3 flex justify-between items-center"
            style="background-color: var(--chat-header-background-color); color: var(--chat-header-text-color);">
            <div class="w-1/4"></div>
            <h1 class="text-md font-bold text-center w-1/2 flex items-center justify-center">
                <img v-if="config.logo" :src="config.logo" class="h-6 mr-2 rounded-full" />
                <span>{{ config.chatbot_title }}</span>
            </h1>
            <div class="w-1/4 flex justify-end">
                <button v-if="config.show_reset_button"
                    class="btn btn-xs bg-black/10 border-none text-current hover:bg-black/20">
                    Reset
                </button>
            </div>
        </header>

        <main class="p-4 text-sm" style="background-color: var(--chat-background-color); height: 400px;">
            <div class="flex justify-start mb-3">
                <div class="px-4 py-2 rounded-2xl"
                    style="background-color: var(--chat-bot-message-background-color); color: var(--chat-bot-message-text-color);">
                    Welcome! How can I help you today?
                </div>
            </div>
            <div class="flex justify-end mb-3">
                <div class="px-4 py-2 rounded-2xl"
                    style="background-color: var(--chat-user-message-background-color); color: var(--chat-user-message-text-color);">
                    Tell me about your services.
                </div>
            </div>
            <div class="flex justify-start">
                <div class="px-4 py-2 rounded-2xl flex items-center space-x-1.5"
                    style="background-color: var(--chat-bot-message-background-color); color: var(--chat-bot-message-text-color);">
                    <span class="w-2 h-2 bg-current/50 rounded-full animate-pulse"></span>
                    <span class="w-2 h-2 bg-current/50 rounded-full animate-pulse"
                        style="animation-delay: 200ms;"></span>
                    <span class="w-2 h-2 bg-current/50 rounded-full animate-pulse"
                        style="animation-delay: 400ms;"></span>
                </div>
            </div>
        </main>

        <footer class="p-3" style="background-color: var(--chat-header-background-color);">
            <div class="flex">
                <input type="text" placeholder="Ask a question..."
                    class="flex-grow border p-2 text-sm focus:outline-none focus:ring-2" :style="chatInputStyle">
                <button class="font-bold py-2 px-4" :style="sendButtonStyle">
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
        '--chat-input-background-color': findColor(styles.input_background_color, '#FFFFFF'),
        '--chat-input-text-color': findColor(styles.input_text_color, '#1F2937'),
        '--chat-input-focus-ring-color': findColor(styles.input_focus_ring_color, '#A855F7'),
        '--chat-background-color': findColor(styles.chat_background_color, '#FFFFFF'),
        '--chat-border-radius': '16px',
    };
});

// Simplified styles for the input and button elements
const chatInputStyle = computed(() => ({
    backgroundColor: 'var(--chat-input-background-color)',
    color: 'var(--chat-input-text-color)',
    borderColor: 'var(--chat-header-background-color)',
    borderTopLeftRadius: 'var(--chat-border-radius)',
    borderBottomLeftRadius: 'var(--chat-border-radius)',
    '--tw-ring-color': 'var(--chat-input-focus-ring-color)'
}));

const sendButtonStyle = computed(() => ({
    backgroundColor: 'var(--chat-send-button-background-color)',
    color: 'var(--chat-send-button-text-color)',
    borderTopRightRadius: 'var(--chat-border-radius)',
    borderBottomRightRadius: 'var(--chat-border-radius)',
}));
</script>