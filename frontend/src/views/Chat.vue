<template>
    <div id="test-chat"
        class="min-h-screen bg-base-200 text-base-content font-sans flex items-center justify-center p-4">
        <div class="flex flex-col w-full max-w-4xl h-[90vh] bg-base-100 rounded-2xl shadow-2xl">
            <header class="bg-base-300/50 p-4 shadow-md z-10 rounded-t-2xl flex justify-between items-center">
                <div class="w-1/4"></div> <!-- Spacer -->
                <h1 class="text-xl font-bold text-center w-1/2 flex items-center justify-center">
                    <font-awesome-icon :icon="['fas', 'comments']" class="mr-3 text-primary" />
                    Chat
                </h1>
                <div class="w-1/4 flex justify-end">
                    <button @click="resetChat" class="btn btn-secondary btn-sm">
                        <font-awesome-icon :icon="['fas', 'arrows-rotate']" class="mr-2" />
                        Reset
                    </button>
                </div>
            </header>

            <main class="flex-grow p-4 overflow-y-auto" ref="chatContainer">
                <div v-for="(message, index) in chatHistory" :key="index"
                    :class="message.isUser ? 'flex justify-end' : 'flex justify-start'">
                    <div class="max-w-xl lg:max-w-2xl px-5 py-3 rounded-2xl mb-3 shadow-md"
                        :class="message.isUser ? 'bg-primary text-primary-content' : 'bg-secondary text-primary'">
                        <div v-if="message.isUser" class="whitespace-pre-wrap">{{ message.text }}</div>
                        <div v-else class="prose prose-sm prose-neutral invert max-w-none whitespace-pre-wrap"
                            v-html="message.html"></div>
                    </div>
                </div>
                <div v-if="isThinking" class="flex justify-start">
                    <div
                        class="max-w-xl lg:max-w-2xl px-5 py-3 rounded-2xl mb-3 bg-secondary flex items-center space-x-2">
                        <span class="w-3 h-3 bg-secondary-content/50 rounded-full animate-pulse"></span>
                        <span class="w-3 h-3 bg-secondary-content/50 rounded-full animate-pulse"
                            style="animation-delay: 200ms;"></span>
                        <span class="w-3 h-3 bg-secondary-content/50 rounded-full animate-pulse"
                            style="animation-delay: 400ms;"></span>
                    </div>
                </div>
            </main>

            <footer class="p-4 bg-base-300/50 rounded-b-2xl">
                <div class="flex">
                    <input type="text" v-model="userMessage" @keyup.enter="sendMessage" placeholder="Ask a question..."
                        class="flex-grow bg-base-200 border border-base-300 rounded-l-lg p-3 focus:outline-none focus:ring-2 focus:ring-primary">
                    <button @click="sendMessage" :disabled="!userMessage.trim() || isThinking"
                        class="bg-primary text-primary-content font-bold py-3 px-5 rounded-r-lg disabled:opacity-50 disabled:bg-neutral">
                        <font-awesome-icon :icon="['fas', 'paper-plane']" />
                    </button>
                </div>
            </footer>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { marked } from 'marked';

const processBotMessage = (content) => {
    try {
        if (typeof content !== 'string') {
            console.error("processBotMessage received non-string content:", content);
            return { text: '', html: '' };
        }
        const cleanedText = content.replace(/{:target="_blank"}/g, '');
        const html = marked(cleanedText);
        return { text: cleanedText, html };
    } catch (e) {
        console.error("Error parsing content with marked.js:", e);
        console.error("Original content:", content);
        return { text: content, html: content };
    }
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const route = useRoute();
const tenantId = ref(route.params.tenantId);
const chatHistory = ref([]);
const userMessage = ref('');
const isThinking = ref(false);
const chatContainer = ref(null);

// --- Cookie Management for Chat History ---
const CHAT_COOKIE_KEY = `chatHistory_${tenantId.value}`;

const saveChatHistoryToCookie = (history) => {
    if (!history || history.length === 0) {
        document.cookie = `${CHAT_COOKIE_KEY}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        return;
    }
    const jsonHistory = JSON.stringify(history);
    const d = new Date();
    d.setTime(d.getTime() + (24 * 60 * 60 * 1000)); // Expires in 1 day
    let expires = "expires=" + d.toUTCString();
    document.cookie = `${CHAT_COOKIE_KEY}=${encodeURIComponent(jsonHistory)};${expires};path=/`;
};

const loadChatHistoryFromCookie = () => {
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
                console.error("Error parsing chat history from cookie:", e);
                return null;
            }
        }
    }
    return null;
};

watch(chatHistory, (newHistory) => {
    saveChatHistoryToCookie(newHistory);
}, { deep: true });


const scrollToBottom = async () => {
    await nextTick();
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
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
                const newHistory = task_result.chat_history;
                chatHistory.value = newHistory.map(msg => {
                    if (msg.type === 'ai') {
                        const { text, html } = processBotMessage(msg.content);
                        return { text, html, isUser: false };
                    }
                    return { text: msg.content, html: null, isUser: true };
                });
                saveChatHistoryToCookie(chatHistory.value);
                isThinking.value = false;
                await scrollToBottom();
            } else if (task_status === 'FAILURE') {
                clearInterval(interval);
                const errorMsg = `Error: Processing failed. ${task_result?.exc_message || ''}`;
                const { text, html } = processBotMessage(errorMsg);
                chatHistory.value.push({ text, html, isUser: false });
                isThinking.value = false;
                await scrollToBottom();
            }
            // If status is PENDING, do nothing and let the interval continue.
        } catch (error) {
            clearInterval(interval);
            const errorMsg = `Error: Could not get task status.`;
            const { text, html } = processBotMessage(errorMsg);
            chatHistory.value.push({ text, html, isUser: false });
            isThinking.value = false;
            await scrollToBottom();
        }
    }, 1000); // Poll once per second
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
            chat_history: historyForBackend
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
    fetchIntroMessage();
};

onMounted(() => {
    const savedHistory = loadChatHistoryFromCookie();
    if (savedHistory && savedHistory.length > 0) {
        chatHistory.value = savedHistory;
        scrollToBottom();
    } else {
        fetchIntroMessage();
    }

    // --- Handle Link Clicks ---
    if (chatContainer.value) {
        chatContainer.value.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href) {
                // Open external links in a new tab
                if (link.hostname !== window.location.hostname) {
                    e.preventDefault();
                    window.open(link.href, '_blank', 'noopener,noreferrer');
                }
            }
        });
    }
});
</script>

<style>
.prose-invert a {
    color: theme('colors.primary');
    text-decoration: underline;
}

.prose-invert a:hover {
    color: theme('colors.primary-focus');
}
</style>
