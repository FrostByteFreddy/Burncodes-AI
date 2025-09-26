<template>
    <div id="test-chat" class="bg-base-200 text-base-content font-sans flex items-center justify-center sm:p-4 p-2">
        <BaseChat v-if="tenant && tenant.widget_config" :config="tenant.widget_config" :chatHistory="chatHistory"
            :isThinking="isThinking" v-model:userMessage="userMessage" @sendMessage="sendMessage" @reset="resetChat" />
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { processBotMessage } from '@/utils/chatProcessor.js';
import { v4 as uuidv4 } from 'uuid';
import BaseChat from '@/components/chat/BaseChat.vue';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const route = useRoute();
const tenantId = ref(route.params.tenantId);
const tenant = ref(null);
const chatHistory = ref([]);
const userMessage = ref('');
const isThinking = ref(false);
const chatContainer = ref(null);
const conversationId = ref(uuidv4());

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
/* All styles are now in BaseChat.vue */
</style>