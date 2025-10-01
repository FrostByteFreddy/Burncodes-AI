<template>
    <div class="chat-widget" :style="widgetCssVariables">
        <header class="chat-header">
            <div class="w-1/4"></div>
            <h1 class="text-md font-bold text-center w-1/2 flex items-center justify-center">
                <img v-if="config.logo" :src="config.logo" class="h-6 mr-2" />
                <span>{{ config.chatbot_title }}</span>
            </h1>
            <div class="w-1/4 flex justify-end">
                <button v-if="config.show_reset_button" @click="$emit('reset')"
                    class="btn btn-secondary btn-xs btn-square rounded-full aspect-square">
                    <font-awesome-icon :icon="['fas', 'arrows-rotate']" />
                </button>
            </div>
        </header>

        <main class="chat-main" ref="chatContainer">
            <div v-for="(message, index) in chatHistory" :key="index"
                :class="[message.isUser ? 'flex justify-end' : 'flex justify-start', 'mb-3']">
                <div class="max-w-xl lg:max-w-2xl px-5 py-3 shadow-md"
                    :class="message.isUser ? 'user-message' : 'bot-message'">
                    <div v-if="message.isUser" class="whitespace-pre-wrap">{{ message.text }}</div>
                    <!-- Use a function to process the HTML and add target="_blank" to links -->
                    <div v-else class="prose prose-sm prose-neutral max-w-none bot-message-prose" v-html="processBotMessage(message.html)">
                    </div>
                </div>
            </div>

            <div v-if="isThinking" class="flex justify-start">
                <div class="max-w-xl lg:max-w-2xl px-5 py-3 shadow-md flex items-center space-x-2 bot-message">
                    <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce thinking-dot"></span>
                    <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce thinking-dot"
                        style="animation-delay: 150ms;"></span>
                    <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce thinking-dot"
                        style="animation-delay: 300ms;"></span>
                </div>
            </div>
        </main>

        <footer class="chat-footer">
            <div class="flex gap-1">
                <input type="text" :value="userMessage" @input="$emit('update:userMessage', $event.target.value)"
                    @keyup.enter="$emit('sendMessage')" placeholder="Ask a question..."
                    class="chat-input flex-grow border px-5 py-3 text-sm focus:outline-none focus:ring-2 rounded-full">
                <button @click="$emit('sendMessage')" :disabled="!userMessage.trim() || isThinking"
                    class="send-button font-bold py-2 px-4 btn-secondary btn-square rounded-full aspect-square">
                    <font-awesome-icon :icon="['fas', 'paper-plane']" />
                </button>
            </div>
        </footer>
    </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue';

const props = defineProps({
    config: {
        type: Object,
        required: true
    },
    chatHistory: {
        type: Array,
        required: true
    },
    isThinking: {
        type: Boolean,
        default: false
    },
    userMessage: {
        type: String,
        default: ''
    }
});

defineEmits(['update:userMessage', 'sendMessage', 'reset']);

const chatContainer = ref(null);

/**
 * Processes the bot's HTML message to make all links open in a new tab.
 * @param {string} html - The HTML content from the bot.
 * @returns {string} The modified HTML string.
 */
const processBotMessage = (html) => {
    if (!html) return '';
    // Use the browser's DOM parser to safely manipulate the HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // Find all anchor tags
    const links = doc.querySelectorAll('a');

    // Add target="_blank" and rel="noopener noreferrer" for security and functionality
    links.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });

    // Return the modified HTML from the body of the parsed document
    return doc.body.innerHTML;
};


const scrollToBottom = async () => {
    await nextTick();
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
};

watch(() => props.chatHistory, scrollToBottom, { deep: true });
watch(() => props.isThinking, scrollToBottom);


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
        '--chat-border-radius': '32px',
    };
});
</script>

<style scoped>
.chat-widget {
    border-radius: var(--chat-border-radius);
    overflow: hidden;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    display: flex;
    flex-direction: column;
    height: 100%;
}

.chat-header {
    background-color: var(--chat-header-background-color);
    color: var(--chat-header-text-color);
    padding: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top-left-radius: var(--chat-border-radius);
    border-top-right-radius: var(--chat-border-radius);
}

.chat-main {
    background-color: var(--chat-background-color);
    padding: 1rem;
    flex-grow: 1;
    overflow-y: auto;
    height: 400px;
}

.user-message {
    background-color: var(--chat-user-message-background-color);
    border-radius: var(--chat-border-radius);
    font-size: .875rem; /* Same as .prose */
}

.bot-message {
    background-color: var(--chat-bot-message-background-color);
    border-radius: var(--chat-border-radius);
}

.user-message, .user-message * {
    color: var(--chat-user-message-text-color) !important;
}

.bot-message, .bot-message * {
    color: var(--chat-bot-message-text-color) !important;
}

.bot-message-prose a {
    color: var(--chat-bot-message-text-color);
    text-decoration: underline;
}

.bot-message-prose a:hover {
    opacity: 0.8;
}

.thinking-dot {
    background-color: var(--chat-bot-message-text-color);
    opacity: .75;
    position: relative;
    top: 3px;
}

.chat-footer {
    background-color: var(--chat-header-background-color);
    padding: 0.75rem;
    border-bottom-left-radius: var(--chat-border-radius);
    border-bottom-right-radius: var(--chat-border-radius);
}

.chat-input {
    background-color: var(--chat-input-background-color);
    color: var(--chat-input-text-color);
    border-color: var(--chat-header-background-color);
    --tw-ring-color: var(--chat-input-focus-ring-color);
}

.chat-input::placeholder {
    color: var(--chat-input-text-color);
    opacity: 0.8;
}

.send-button {
    background-color: var(--chat-send-button-background-color);
    color: var(--chat-send-button-text-color);
}
</style>
