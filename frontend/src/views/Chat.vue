<template>
    <div class="flex flex-col h-screen bg-gray-900 text-white font-sans">
        <header class="bg-gray-800 p-4 shadow-md z-10">
            <h1 class="text-xl font-bold text-center">Chat with {{ tenantId }}</h1>
        </header>

        <main class="flex-grow p-4 overflow-y-auto" ref="chatContainer">
            <div v-for="(message, index) in chatHistory" :key="index"
                :class="message.isUser ? 'flex justify-end' : 'flex justify-start'">
                <div class="max-w-xl lg:max-w-2xl px-5 py-3 rounded-2xl mb-3 shadow-md"
                    :class="message.isUser ? 'bg-gradient-to-br from-orange-600 to-red-700' : 'bg-gray-700'">
                    <div v-if="message.isUser" class="whitespace-pre-wrap">{{ message.text }}</div>
                    <div v-else class="prose prose-invert max-w-none" v-html="message.html"></div>
                </div>
            </div>
            <div v-if="isThinking" class="flex justify-start">
                <div class="max-w-xl lg:max-w-2xl px-5 py-3 rounded-2xl mb-3 bg-gray-700 flex items-center space-x-2">
                    <span class="w-3 h-3 bg-gray-500 rounded-full animate-pulse"></span>
                    <span class="w-3 h-3 bg-gray-500 rounded-full animate-pulse" style="animation-delay: 200ms;"></span>
                    <span class="w-3 h-3 bg-gray-500 rounded-full animate-pulse" style="animation-delay: 400ms;"></span>
                </div>
            </div>
        </main>

        <footer class="p-4 bg-gray-800">
            <div class="flex">
                <input type="text" v-model="userMessage" @keyup.enter="sendMessage"
                    placeholder="Ask a question..."
                    class="flex-grow bg-gray-700 border border-gray-600 rounded-l-lg p-3 focus:outline-none focus:ring-2 focus:ring-orange-500">
                <button @click="sendMessage" :disabled="!userMessage.trim()"
                    class="bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 disabled:from-gray-600 text-white font-bold py-3 px-5 rounded-r-lg">
                    Send
                </button>
            </div>
        </footer>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { marked } from 'marked';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const route = useRoute();
const tenantId = ref(route.params.tenantId);
const chatHistory = ref([]);
const userMessage = ref('');
const isThinking = ref(false);
const chatContainer = ref(null);

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
        const introMsg = response.data.intro_message;
        chatHistory.value.push({
            text: introMsg,
            html: marked(introMsg),
            isUser: false
        });
    } catch (error) {
        const errorMsg = `Error: ${error.response?.data?.error || 'Could not get initial message.'}`;
        chatHistory.value.push({ text: errorMsg, html: marked(errorMsg), isUser: false });
    } finally {
        isThinking.value = false;
        await scrollToBottom();
    }
};

const sendMessage = async () => {
    if (!userMessage.value.trim() || !tenantId.value) return;

    const currentMessage = userMessage.value;
    const historyForBackend = chatHistory.value.map(msg => ({
        type: msg.isUser ? 'human' : 'ai',
        content: msg.text
    }));

    chatHistory.value.push({ text: currentMessage, html: currentMessage, isUser: true });
    userMessage.value = '';
    isThinking.value = true;
    await scrollToBottom();

    try {
        const payload = {
            query: currentMessage,
            chat_history: historyForBackend
        };
        const response = await axios.post(`${API_BASE_URL}/chat/${tenantId.value}`, payload);
        const newHistory = response.data.chat_history;

        chatHistory.value = newHistory.map(msg => ({
            text: msg.content,
            html: msg.type === 'ai' ? marked(msg.content) : null,
            isUser: msg.type === 'human'
        }));

    } catch (error) {
        const errorMsg = `Error: ${error.response?.data?.error || 'Could not get a response.'}`;
        chatHistory.value.push({ text: errorMsg, html: marked(errorMsg), isUser: false });
    } finally {
        isThinking.value = false;
        await scrollToBottom();
    }
};

onMounted(() => {
    fetchIntroMessage();
});
</script>

<style>
.prose-invert a {
    color: #fb923c; /* orange-400 */
    text-decoration: underline;
}
.prose-invert a:hover {
    color: #fdba74; /* orange-300 */
}
</style>
