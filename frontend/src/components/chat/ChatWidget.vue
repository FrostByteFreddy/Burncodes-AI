<template>
  <!-- Collapsed state (non-widget mode only — in widget mode parent hides the iframe) -->
  <div v-if="!isChatOpen" class="chat-collapsed-bar" @click="isChatOpen = true">
    <span>{{ resolvedConfig.chatbot_title || 'Chat' }}</span>
    <font-awesome-icon :icon="['fas', 'chevron-up']" />
  </div>

  <BaseChat
    v-else
    :config="resolvedConfig"
    :chatHistory="chatHistory"
    :isThinking="isThinking"
    :isWidget="isWidget"
    v-model:userMessage="userMessage"
    @sendMessage="sendMessage"
    @reset="resetChat"
    @close="handleClose"
  />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import BaseChat from './BaseChat.vue';
import { processBotMessage } from '@/utils/chatProcessor.js';

const { t } = useI18n();

const props = defineProps({
  /** Pass tenantId to fetch config from the public API (standalone page mode) */
  tenantId: { type: String, default: null },
  /** Pass config directly to skip the API fetch (preview mode — live reactive updates) */
  config: { type: Object, default: null },
  isWidget: { type: Boolean, default: false },
});

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// ── Config resolution ──────────────────────────────────────────────────────────
const fetchedConfig = ref(null);
const resolvedConfig = computed(() => props.config ?? fetchedConfig.value ?? {});

// ── Open / close state ────────────────────────────────────────────────────────
const isChatOpen = ref(true);

const handleClose = () => {
  if (props.isWidget) {
    // Tell widget.js to hide the iframe; the launcher re-opens it
    window.parent.postMessage({ type: 'burncodes:close-widget' }, '*');
  } else {
    isChatOpen.value = false;
  }
};

// ── Chat state ─────────────────────────────────────────────────────────────────
const chatHistory    = ref([]);
const userMessage    = ref('');
const isThinking     = ref(false);
const conversationId = ref(uuidv4());
const activeAbortController = ref(null);

// ── Session persistence (standalone only) ──────────────────────────────────────
const storageKey = computed(() => props.tenantId ? `chatSession_${props.tenantId}` : null);

const saveSession = (history, convId) => {
  if (!storageKey.value) return;
  if (!history?.length) { sessionStorage.removeItem(storageKey.value); return; }
  try { sessionStorage.setItem(storageKey.value, JSON.stringify({ history, conversationId: convId })); }
  catch { /* storage full — ignore */ }
};

const loadSession = () => {
  if (!storageKey.value) return null;
  try { const raw = sessionStorage.getItem(storageKey.value); return raw ? JSON.parse(raw) : null; }
  catch { return null; }
};

// ── Fetch config (standalone mode only) ───────────────────────────────────────
const fetchConfig = async () => {
  if (!props.tenantId || props.config) return;
  try {
    const { data } = await axios.get(`${API_BASE_URL}/tenants/${props.tenantId}/public`);
    fetchedConfig.value = data.widget_config || {};
  } catch (err) {
    console.error('[ChatWidget] Failed to fetch tenant config', err);
  }
};

// ── Intro message ─────────────────────────────────────────────────────────────
const fetchIntroMessage = async () => {
  if (!props.tenantId) return;
  isThinking.value = true;
  try {
    const { data } = await axios.get(`${API_BASE_URL}/chat/${props.tenantId}/intro`);
    const { text, html } = processBotMessage(data.intro_message);
    chatHistory.value.push({ text, html, isUser: false });
    saveSession(chatHistory.value, conversationId.value);
  } catch (err) {
    const { text, html } = processBotMessage(`Error: ${err.response?.data?.error || t('chat.errors.initialMessage')}`);
    chatHistory.value.push({ text, html, isUser: false });
    saveSession(chatHistory.value, conversationId.value);
  } finally {
    isThinking.value = false;
  }
};

// ── Task polling ──────────────────────────────────────────────────────────────
const pollTaskStatus = (taskId) => {
  let retries = 0;
  const MAX_RETRIES = 4;

  const longPoll = async () => {
    if (retries >= MAX_RETRIES) {
      isThinking.value = false;
      const { text, html } = processBotMessage(t('chat.errors.taskStatus'));
      chatHistory.value.push({ text, html, isUser: false });
      saveSession(chatHistory.value, conversationId.value);
      return;
    }
    retries++;
    const controller = new AbortController();
    activeAbortController.value = controller;

    try {
      const { data } = await axios.get(
        `${API_BASE_URL}/chat/task/${taskId}/status?timeout=25`,
        { signal: controller.signal, timeout: 30000 }
      );
      const { state: task_status, result: task_result } = data;

      if (task_status === 'SUCCESS') {
        activeAbortController.value = null;
        isThinking.value = false;

        const fullHistory = task_result.chat_history;
        const last = fullHistory[fullHistory.length - 1];

        if (last?.type === 'ai') {
          chatHistory.value = fullHistory.slice(0, -1).map(msg =>
            msg.type === 'ai'
              ? { ...processBotMessage(msg.content), isUser: false }
              : { text: msg.content, html: null, isUser: true }
          );
          chatHistory.value.push({ text: '', html: '', isUser: false });

          const current = chatHistory.value[chatHistory.value.length - 1];
          for (const part of last.content.split(/(\s+)/)) {
            current.text += part;
            current.html = processBotMessage(current.text).html;
            await new Promise(r => setTimeout(r, Math.random() * 5));
          }
        } else {
          chatHistory.value = fullHistory.map(msg =>
            msg.type === 'ai'
              ? { ...processBotMessage(msg.content), isUser: false }
              : { text: msg.content, html: null, isUser: true }
          );
        }
        saveSession(chatHistory.value, conversationId.value);
        return;
      }

      if (task_status === 'FAILURE') {
        activeAbortController.value = null;
        const { text, html } = processBotMessage(`${t('chat.errors.processingFailed')} ${task_result?.exc_message || ''}`);
        chatHistory.value.push({ text, html, isUser: false });
        saveSession(chatHistory.value, conversationId.value);
        isThinking.value = false;
        return;
      }

      await longPoll();
    } catch (err) {
      if (axios.isCancel(err)) return;
      activeAbortController.value = null;
      const { text, html } = processBotMessage(t('chat.errors.taskStatus'));
      chatHistory.value.push({ text, html, isUser: false });
      saveSession(chatHistory.value, conversationId.value);
      isThinking.value = false;
    }
  };

  longPoll();
};

// ── Send message ──────────────────────────────────────────────────────────────
const sendMessage = async () => {
  if (!userMessage.value.trim() || !props.tenantId || isThinking.value) return;

  const current = userMessage.value;
  const historyForBackend = chatHistory.value.map(m => ({
    type: m.isUser ? 'human' : 'ai',
    content: m.text,
  }));

  chatHistory.value.push({ text: current, html: null, isUser: true });
  saveSession(chatHistory.value, conversationId.value);
  userMessage.value = '';
  isThinking.value = true;

  try {
    const { data } = await axios.post(`${API_BASE_URL}/chat/${props.tenantId}`, {
      query: current,
      chat_history: historyForBackend,
      conversation_id: conversationId.value,
    });
    if (data.task_id) {
      pollTaskStatus(data.task_id);
    } else {
      throw new Error('No task_id received');
    }
  } catch (err) {
    const { text, html } = processBotMessage(`Error: ${err.response?.data?.error || t('chat.errors.sendMessage')}`);
    chatHistory.value.push({ text, html, isUser: false });
    saveSession(chatHistory.value, conversationId.value);
    isThinking.value = false;
  }
};

// ── Reset ─────────────────────────────────────────────────────────────────────
const resetChat = () => {
  chatHistory.value = [];
  conversationId.value = uuidv4();
  saveSession([], null);
  fetchIntroMessage();
};

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  await fetchConfig();

  if (props.tenantId) {
    const session = loadSession();
    if (session?.history?.length) {
      chatHistory.value = session.history;
      conversationId.value = session.conversationId || uuidv4();
    } else {
      conversationId.value = uuidv4();
      await fetchIntroMessage();
    }
  }
});

onUnmounted(() => {
  if (activeAbortController.value) {
    activeAbortController.value.abort();
    activeAbortController.value = null;
  }
});
</script>

<style scoped>
.chat-collapsed-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--chat-header-background-color, #6366f1);
  color: var(--chat-header-text-color, #ffffff);
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  user-select: none;
}
</style>
