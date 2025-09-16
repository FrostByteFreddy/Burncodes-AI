<template>
    <div id="app"
        class="bg-gradient-to-br from-black via-gray-900 to-black text-slate-100 min-h-screen font-sans flex flex-col p-4 sm:p-6 lg:p-8">

        <div class="w-full max-w-7xl mx-auto space-y-8">
            <header class="text-center">
                <h1 class="text-5xl font-extrabold tracking-tight">
                    <span
                        class="bg-gradient-to-r from-orange-500 to-red-600 bg-clip-text text-transparent">SwiftAnser</span>
                </h1>
                <p class="mt-2 text-lg text-slate-400">Add documents and URLs, then ask them anything!</p>
            </header>

            <main class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-1 space-y-8">

                    <section
                        class="bg-gray-900/50 backdrop-blur-sm border border-gray-800 p-6 rounded-2xl shadow-2xl shadow-orange-500/10">
                        <h2 class="text-2xl font-bold mb-4 text-orange-400 border-b border-gray-700 pb-3">1. Add
                            Sources</h2>

                        <div class="mb-6">
                            <label for="file-upload" class="block text-sm font-medium text-slate-300 mb-2">Upload
                                Files</label>
                            <label for="file-upload"
                                class="flex w-full cursor-pointer bg-gray-800 hover:bg-gray-700 text-slate-200 font-bold py-3 px-4 rounded-lg transition duration-300 text-center truncate">
                                <span class="flex items-center justify-center mx-auto">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 mr-3" fill="none"
                                        viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                        <path stroke-linecap="round" stroke-linejoin="round"
                                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                    </svg>
                                    Choose files...
                                </span>
                            </label>
                            <input id="file-upload" type="file" @change="handleFileSelect" accept=".pdf,.docx,.txt,.csv"
                                class="hidden" multiple>
                            <div v-if="selectedFiles.length > 0" class="mt-2 text-sm text-slate-400">
                                {{ selectedFiles.length }} file(s) selected. <button @click="handleUpload"
                                    :disabled="isProcessing"
                                    class="text-orange-400 hover:text-orange-300 font-semibold">Process Files</button>
                            </div>
                        </div>

                        <div>
                            <label for="url-input" class="block text-sm font-medium text-slate-300 mb-2">Crawl from
                                URL</label>
                            <div class="flex">
                                <input id="url-input" v-model="urlInput" type="url" placeholder="https://example.com"
                                    class="flex-grow bg-gray-800 border border-gray-700 rounded-l-lg p-3 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50 transition-colors">
                                <button @click="handleCrawlUrl" :disabled="isProcessing || !urlInput.trim()"
                                    class="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white font-bold py-3 px-5 rounded-r-lg transition-colors">Crawl</button>
                            </div>
                        </div>
                    </section>

                    <section
                        class="bg-gray-900/50 backdrop-blur-sm border border-gray-800 p-6 rounded-2xl shadow-2xl shadow-red-500/10">
                        <div class="flex justify-between items-center border-b border-gray-700 pb-3 mb-4">
                            <h2 class="text-2xl font-bold text-red-500">2. Current Context</h2>
                            <button @click="handleClearContext" :disabled="isProcessing"
                                class="text-sm text-slate-400 hover:text-white disabled:opacity-50">Clear All</button>
                        </div>
                        <ul v-if="processedSources.length > 0" class="space-y-2 max-h-40 overflow-y-auto pr-2">
                            <li v-for="(source, index) in processedSources" :key="index"
                                class="bg-gray-800/50 p-3 rounded-lg text-sm truncate flex items-center">
                                <svg xmlns="http://www.w3.org/2000/svg"
                                    class="w-5 h-5 mr-3 text-orange-400 flex-shrink-0" fill="none" viewBox="0 0 24 24"
                                    stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round"
                                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                {{ source }}
                            </li>
                        </ul>
                        <p v-else class="text-slate-500 text-sm">No sources added yet.</p>
                        <p v-if="processingStatus" class="mt-4 text-center font-medium" :class="statusColor">{{
                            processingStatus }}</p>
                    </section>

                </div>

                <div class="lg:col-span-2">
                    <section
                        class="bg-gray-900/50 backdrop-blur-sm border border-gray-800 p-6 rounded-2xl shadow-2xl shadow-red-500/10 flex flex-col h-[80vh]">
                        <h2 class="text-2xl font-bold mb-4 text-red-500 border-b border-gray-700 pb-3 flex-shrink-0">
                            3. Chat</h2>

                        <div class="flex-grow overflow-y-auto mb-4 p-4 bg-black/50 rounded-lg min-h-0"
                            ref="chatContainer">
                            <div v-for="(message, index) in chatHistory" :key="index"
                                :class="message.isUser ? 'flex justify-end' : 'flex justify-start'">
                                <div class="max-w-xl lg:max-w-2xl px-5 py-3 rounded-2xl mb-3 shadow-md"
                                    :class="message.isUser ? 'bg-gradient-to-br from-orange-600 to-red-700' : 'bg-gray-700'">
                                    <div v-if="message.isUser" class="text-white whitespace-pre-wrap">{{ message.text }}
                                    </div>
                                    <div v-else class="prose prose-invert max-w-none" v-html="message.html"></div>
                                </div>
                            </div>
                            <div v-if="isThinking" class="flex justify-start">
                                <div
                                    class="max-w-xl lg:max-w-2xl px-5 py-3 rounded-2xl mb-3 bg-gray-700 flex items-center space-x-2">
                                    <span class="w-3 h-3 bg-gray-500 rounded-full animate-pulse"></span>
                                    <span class="w-3 h-3 bg-gray-500 rounded-full animate-pulse"
                                        style="animation-delay: 200ms;"></span>
                                    <span class="w-3 h-3 bg-gray-500 rounded-full animate-pulse"
                                        style="animation-delay: 400ms;"></span>
                                </div>
                            </div>
                        </div>

                        <div class="flex flex-shrink-0">
                            <input type="text" v-model="userMessage" @keyup.enter="sendMessage"
                                placeholder="Ask a question..."
                                :disabled="isProcessing || !tenantId"
                                class="flex-grow bg-gray-800 border border-gray-700 rounded-l-lg p-3 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50 transition-colors">
                            <button @click="sendMessage"
                                :disabled="isProcessing || !tenantId || !userMessage.trim()"
                                class="bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 disabled:from-gray-600 text-white font-bold py-3 px-5 rounded-r-lg transition-all flex items-center">
                                Send
                                <svg class="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                                    xmlns="http://www.w3.org/2000/svg">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                                </svg>
                            </button>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue';
import axios from 'axios';
import { marked } from 'marked';

// --- STATE MANAGEMENT ---
const selectedFiles = ref([]);
const urlInput = ref('');
const processingStatus = ref('');
const isProcessing = ref(false);
const processedSources = ref([]);
const chatHistory = ref([]);
const userMessage = ref('');
const isThinking = ref(false);
const chatContainer = ref(null);
const tenantId = ref(null);

// --- API CONFIGURATION ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api';

// --- LIFECYCLE HOOK ---
onMounted(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tenantFromUrl = urlParams.get('tenant');
    if (tenantFromUrl) {
        tenantId.value = tenantFromUrl;
        console.log(`Tenant initialized: ${tenantId.value}`);
        fetchIntroMessage();
    } else {
        console.error("Tenant ID is missing from URL.");
        processingStatus.value = "Error: Tenant ID is missing from the URL. Please add '?tenant=your_tenant_id' to the address bar.";
    }
});

// --- COMPUTED PROPERTIES ---
const statusColor = computed(() => {
    if (processingStatus.value.includes('Successfully') || processingStatus.value.includes('complete')) return 'text-orange-400';
    if (processingStatus.value.includes('Error')) return 'text-red-400';
    return 'text-slate-400';
});

// --- METHODS ---
function handleFileSelect(event) {
    selectedFiles.value = Array.from(event.target.files);
    processingStatus.value = '';
}

async function handleUpload() {
    if (selectedFiles.value.length === 0 || !tenantId.value) return;
    isProcessing.value = true;
    for (const file of selectedFiles.value) {
        processingStatus.value = `Processing file: ${file.name}...`;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tenant', tenantId.value);
        try {
            await axios.post(`${API_BASE_URL}/upload`, formData);
            processedSources.value.push(`[File] ${file.name}`);
            processingStatus.value = `Successfully added: ${file.name}`;
        } catch (error) {
            processingStatus.value = `Error processing ${file.name}: ${error.response?.data?.error || 'Unknown error'}`;
        }
    }
    selectedFiles.value = [];
    isProcessing.value = false;
}

async function handleCrawlUrl() {
    if (!urlInput.value.trim() || !tenantId.value) return;
    isProcessing.value = true;
    const url = urlInput.value;
    
    // Step 1: Discover links (this remains the same)
    processingStatus.value = `Discovering pages from: ${url}...`;
    let urlsToProcess = [];
    try {
        const discoverPayload = { url, tenant: tenantId.value };
        const response = await axios.post(`${API_BASE_URL}/discover_links`, discoverPayload);
        urlsToProcess = response.data.urls;
        if (!urlsToProcess || urlsToProcess.length === 0) {
            processingStatus.value = "No crawlable pages found at that URL.";
            isProcessing.value = false;
            return;
        }
    } catch (error) {
        console.error("Discovery failed:", error);
        processingStatus.value = `Error discovering links: ${error.response?.data?.error || 'An unknown network error occurred.'}`;
        isProcessing.value = false;
        return;
    }

    // Step 2: Process all discovered URLs in a single batch request
    processingStatus.value = `Found ${urlsToProcess.length} pages. Indexing all in parallel...`;
    try {
        const batchPayload = {
            urls: urlsToProcess,
            tenant: tenantId.value
        };
        const batchResponse = await axios.post(`${API_BASE_URL}/process_url_batch`, batchPayload, { timeout: 7200000 }); // 2h timeout
        
        if (batchResponse.data.success) {
            // Add the newly processed sources to our list in the UI
            const newSources = batchResponse.data.processed_sources || [];
            newSources.forEach(sourceName => {
                 const type = ['.pdf', '.docx', '.txt', '.csv'].some(ext => sourceName.toLowerCase().endsWith(ext)) ? '[File]' : '[Page]';
                 if (!processedSources.value.includes(`${type} ${sourceName}`)) {
                    processedSources.value.push(`${type} ${sourceName}`);
                 }
            });
            processingStatus.value = `Indexing complete. ${newSources.length} new sources added.`;
        } else {
             processingStatus.value = `Processing failed: ${batchResponse.data.message}`;
        }
    } catch (error) {
        console.error("Batch processing failed:", error);
        processingStatus.value = `Error during batch processing: ${error.response?.data?.error || 'A network error occurred.'}`;
    }
    
    urlInput.value = '';
    isProcessing.value = false;
}

async function handleClearContext() {
    if (!tenantId.value) return;
    isProcessing.value = true;
    processingStatus.value = 'Clearing context...';
    try {
        await axios.post(`${API_BASE_URL}/clear`, { tenant: tenantId.value });
        processedSources.value = [];
        chatHistory.value = [];
        processingStatus.value = 'Context cleared successfully.';
        await fetchIntroMessage();
    } catch (error) {
        processingStatus.value = `Error clearing context: ${error.response?.data?.error || 'Unknown error'}`;
    }
    isProcessing.value = false;
}

async function scrollToBottom() {
    await nextTick();
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
}

async function fetchIntroMessage() {
    if (!tenantId.value || chatHistory.value.length > 0) return;

    isThinking.value = true;
    await scrollToBottom();
    try {
        const payload = { tenant: tenantId.value };
        const response = await axios.post(`${API_BASE_URL}/intro`, payload);
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
}

async function sendMessage() {
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
            tenant: tenantId.value,
            chat_history: historyForBackend
        };
        const response = await axios.post(`${API_BASE_URL}/chat`, payload);
        
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
}
</script>

<style>
/* Style section remains unchanged */
body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.overflow-y-auto::-webkit-scrollbar {
    width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
    background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
    background-color: #374151;
    border-radius: 20px;
    border: 3px solid transparent;
}

.prose-invert a {
    color: #fb923c;
    /* orange-400 */
    text-decoration: underline;
}

.prose-invert a:hover {
    color: #fdba74;
    /* orange-300 */
}
</style>