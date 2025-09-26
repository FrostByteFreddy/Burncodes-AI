<template>
    <div id="test-chat"
        class="bg-base-200 text-base-content font-sans flex items-center justify-center sm:p-4">
        <div class="flex flex-col w-full max-w-4xl h-[90vh] shadow-2xl" :style="widgetCssVariables">
            <header class="p-4 shadow-sm z-10 flex justify-between items-center"
                style="background-color: var(--chat-header-background-color); color: var(--chat-header-text-color); border-top-left-radius: var(--chat-border-radius); border-top-right-radius: var(--chat-border-radius);">
                <div class="w-1/4"></div>
                <h1 class="text-xl font-bold text-center w-1/2 flex items-center justify-center">
                    <img v-if="tenant?.widget_config?.logo" :src="tenant.widget_config.logo" class="h-8 mr-3" />
                    {{ tenant?.widget_config?.chatbot_title }}
                </h1>
                <div class="w-1/4 flex justify-end">
                    <button v-if="tenant?.widget_config?.show_reset_button" @click="resetChat"
                        class="btn btn-secondary btn-sm rounded-full aspect-square">
                        <font-awesome-icon :icon="['fas', 'arrows-rotate']" />
                    </button>
                </div>
            </header>

            <main class="flex-grow p-4 overflow-y-auto" ref="chatContainer"
                style="background-color: var(--chat-background-color);">
                <div v-for="(message, index) in chatHistory" :key="index"
                    :class="message.isUser ? 'flex justify-end' : 'flex justify-start'">
                    <div class="max-w-xl lg:max-w-2xl px-5 py-3 mb-3 shadow-md"
                        :style="message.isUser ? userMessageStyle : botMessageStyle">
                        <div v-if="message.isUser" class="whitespace-pre-wrap" :style="userMessageColor">{{ message.text
                            }}</div>
                        <div v-else class="prose prose-sm prose-neutral max-w-none bot-message-prose"
                            :style="botMessageColor" v-html="message.html"></div>
                    </div>
                </div>
                <div v-if="isThinking" class="flex justify-start">
                    <div class="max-w-xl lg:max-w-2xl px-5 py-3 rounded-2xl mb-3 flex items-center space-x-2"
                        :style="botMessageStyle">
                        <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce"
                            :style="botThinkingDotsStyle"></span>
                        <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce" style="animation-delay: 150ms;"
                            :style="botThinkingDotsStyle"></span>
                        <span class="w-3 h-3 bg-current/50 rounded-full animate-bounce" style="animation-delay: 300ms;"
                            :style="botThinkingDotsStyle"></span>
                    </div>
                </div>
            </main>

            <footer class="p-4"
                style="background-color: var(--chat-header-background-color); border-bottom-left-radius: var(--chat-border-radius); border-bottom-right-radius: var(--chat-border-radius);">
                <div class="flex gap-1">
                    <input type="text" v-model="userMessage" @keyup.enter="sendMessage" placeholder="Ask a question..."
                        class="chat-input flex-grow border px-5 py-3 focus:outline-none focus:ring-2 rounded-full"
                        :style="chatInputStyle">

                    <button @click="sendMessage" :disabled="!userMessage.trim() || isThinking"
                        class="send-button disabled:opacity-50 btn btn-secondary btn-square rounded-full aspect-square"
                        :style="sendButtonStyle">
                        <font-awesome-icon :icon="['fas', 'paper-plane']" />
                    </button>
                </div>
            </footer>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { processBotMessage } from '@/utils/chatProcessor.js';
import { v4 as uuidv4 } from 'uuid';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const route = useRoute();
const tenantId = ref(route.params.tenantId);
const tenant = ref(null);
const chatHistory = ref([]);
const userMessage = ref('');
const isThinking = ref(false);
const chatContainer = ref(null);
const conversationId = ref(uuidv4());

// --- Centralized CSS Variable Generator ---
const widgetCssVariables = computed(() => {
    const config = tenant.value?.widget_config;
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
        '--chat-border-radius': '24px',
    };
});

// Corrected and consolidated computed styles
const userMessageStyle = computed(() => ({
    backgroundColor: 'var(--chat-user-message-background-color)',
    color: 'var(--chat-user-message-text-color)',
    borderRadius: 'var(--chat-border-radius)',
}));

// Prose override
const userMessageColor = computed(() => ({
    color: 'var(--chat-user-message-text-color) !important',
}));

const botMessageStyle = computed(() => ({
    backgroundColor: 'var(--chat-bot-message-background-color)',
    color: 'var(--chat-bot-message-text-color)',
    borderRadius: 'var(--chat-border-radius)',
}));

// Prose override
const botMessageColor = computed(() => ({
    color: 'var(--chat-bot-message-text-color) !important',
}));

const botThinkingDotsStyle = computed(() => ({
    backgroundColor: 'var(--chat-bot-message-text-color',
    opacity: '.75'
}));

const chatInputStyle = computed(() => ({
    backgroundColor: 'var(--chat-input-background-color)',
    color: 'var(--chat-input-text-color)',
    borderColor: 'var(--chat-header-background-color)',
    '--tw-ring-color': 'var(--chat-input-focus-ring-color)' // For Tailwind's focus ring
}));

const sendButtonStyle = computed(() => ({
    backgroundColor: 'var(--chat-send-button-background-color)',
    color: 'var(--chat-send-button-text-color)',
}));

// --- Cookie Management for Chat History ---
const CHAT_COOKIE_KEY = `chatSession_${tenantId.value}`;

const saveChatToCookie = (history, convId) => {
    if (!history || history.length === 0) {
        document.cookie = `${CHAT_COOKIE_KEY}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        return;
    }
    const sessionData = JSON.stringify({ history, conversationId: convId });
    const d = new Date();
    d.setTime(d.getTime() + (24 * 60 * 60 * 1000)); // Expires in 1 day
    let expires = "expires=" + d.toUTCString();
    document.cookie = `${CHAT_COOKIE_KEY}=${encodeURIComponent(sessionData)};${expires};path=/;SameSite=Lax`;
};

const loadChatFromCookie = () => {
    const name = CHAT_COOKIE_KEY + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            try {
                return JSON.parse(decodeURIComponent(c.substring(name.length, c.length)));
            } catch (e) {
                console.error("Error parsing chat session from cookie:", e);
                return null;
            }
        }
    }
    return null;
};

watch(chatHistory, (newHistory) => {
    saveChatToCookie(newHistory, conversationId.value);
}, { deep: true });


const scrollToBottom = async () => {
    await nextTick();
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
};

const fetchTenant = async () => {
    if (!tenantId.value) return;
    try {
        const response = await axios.get(`${API_BASE_URL}/tenants/${tenantId.value}/public`);
        tenant.value = response.data;
    } catch (error) {
        console.error('Failed to fetch tenant config', error);
    }
};

const fetchIntroMessage = async () => {
    if (!tenantId.value) return;
    isThinking.value = true;
    await scrollToBottom();
    try {
        const response = await axios.get(`${API_BASE_URL}/chat/${tenantId.value}/intro`);
        const { text, html } = processBotMessage(response.data.intro_message);
        chatHistory.value.push({ text, html, isUser: false });
    } catch (error) {
        const errorMsg = `Error: ${error.response?.data?.error || 'Could not get initial message.'}`;
        const { text, html } = processBotMessage(errorMsg);
        chatHistory.value.push({ text, html, isUser: false });
    } finally {
        isThinking.value = false;
        await scrollToBottom();
    }
};

const pollTaskStatus = (taskId) => {
    const interval = setInterval(async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/chat/task/${taskId}/status`);
            const { state: task_status, result: task_result } = response.data;

            if (task_status === 'SUCCESS') {
                clearInterval(interval);
                isThinking.value = false;
                await scrollToBottom(); // Scroll down after the "thinking" dots disappear

                const fullHistory = task_result.chat_history;
                const lastMessageFromServer = fullHistory[fullHistory.length - 1];

                if (lastMessageFromServer && lastMessageFromServer.type === 'ai') {
                    const previousHistory = fullHistory.slice(0, -1);
                    chatHistory.value = previousHistory.map(msg => {
                        if (msg.type === 'ai') {
                            const { text, html } = processBotMessage(msg.content);
                            return { text, html, isUser: false };
                        }
                        return { text: msg.content, html: null, isUser: true };
                    });

                    chatHistory.value.push({ text: '', html: '', isUser: false });
                    await nextTick(); // Ensure the empty message div is in the DOM

                    const fullBotResponseText = lastMessageFromServer.content;
                    const wordsAndSpaces = fullBotResponseText.split(/(\s+)/);
                    const currentBotMessage = chatHistory.value[chatHistory.value.length - 1];

                    for (const part of wordsAndSpaces) {
                        currentBotMessage.text += part;
                        currentBotMessage.html = processBotMessage(currentBotMessage.text).html;

                        await scrollToBottom();

                        const delay = Math.random() * (10 - 5);
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                } else {
                    chatHistory.value = fullHistory.map(msg => {
                        if (msg.type === 'ai') {
                            const { text, html } = processBotMessage(msg.content);
                            return { text, html, isUser: false };
                        }
                        return { text: msg.content, html: null, isUser: true };
                    });
                    await scrollToBottom();
                }
            } else if (task_status === 'FAILURE') {
                clearInterval(interval);
                const errorMsg = `Error: Processing failed. ${task_result?.exc_message || ''}`;
                const { text, html } = processBotMessage(errorMsg);
                chatHistory.value.push({ text, html, isUser: false });
                isThinking.value = false;
                await scrollToBottom();
            }
        } catch (error) {
            clearInterval(interval);
            const errorMsg = `Error: Could not get task status.`;
            const { text, html } = processBotMessage(errorMsg);
            chatHistory.value.push({ text, html, isUser: false });
            isThinking.value = false;
            await scrollToBottom();
        }
    }, 1000);
};

const sendMessage = async () => {
    if (!userMessage.value.trim() || !tenantId.value || isThinking.value) return;

    const currentMessage = userMessage.value;
    const historyForBackend = chatHistory.value.map(msg => ({
        type: msg.isUser ? 'human' : 'ai',
        content: msg.text
    }));

    chatHistory.value.push({ text: currentMessage, html: null, isUser: true });
    userMessage.value = '';
    isThinking.value = true;
    await scrollToBottom();

    try {
        const payload = {
            query: currentMessage,
            chat_history: historyForBackend,
            conversation_id: conversationId.value
        };
        const response = await axios.post(`${API_BASE_URL}/chat/${tenantId.value}`, payload);
        const { task_id } = response.data;
        if (task_id) {
            pollTaskStatus(task_id);
        } else {
            throw new Error("No task_id received from the server.");
        }
    } catch (error) {
        const errorMsg = `Error: ${error.response?.data?.error || 'Could not send message.'}`;
        const { text, html } = processBotMessage(errorMsg);
        chatHistory.value.push({ text, html, isUser: false });
        isThinking.value = false;
        await scrollToBottom();
    }
};

const resetChat = () => {
    chatHistory.value = [];
    conversationId.value = uuidv4();
    saveChatToCookie([], null);
    fetchIntroMessage();
};

onMounted(async () => {
    await fetchTenant();
    const sessionData = loadChatFromCookie();
    if (sessionData && sessionData.history && sessionData.history.length > 0) {
        chatHistory.value = sessionData.history;
        conversationId.value = sessionData.conversationId || uuidv4();
        scrollToBottom();
    } else {
        conversationId.value = uuidv4();
        fetchIntroMessage();
    }

    if (chatContainer.value) {
        chatContainer.value.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href && link.hostname !== window.location.hostname) {
                e.preventDefault();
                window.open(link.href, '_blank', 'noopener,noreferrer');
            }
        });
    }
});
</script>

<style scoped>
.bot-message-prose a {
    color: var(--chat-bot-message-text-color);
    text-decoration: underline;
}

.bot-message-prose a:hover {
    opacity: 0.8;
}

.chat-input::placeholder {
    color: var(--chat-input-text-color);
    opacity: 0.8;
}
</style>