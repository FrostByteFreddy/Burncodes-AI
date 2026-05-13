<template>
  <!-- Collapsed state (non-widget mode only — in widget mode the parent hides the iframe) -->
  <div
    v-if="!isChatOpen"
    class="chat-launcher"
    :style="{ backgroundColor: launcherBgColor }"
    @click="isChatOpen = true"
    :title="resolvedConfig.chatbot_title || 'Chat'"
  >
    <img
      v-if="resolvedConfig.launcher_icon"
      :src="resolvedConfig.launcher_icon"
      class="chat-launcher__icon"
      alt="Open chat"
    />
    <svg
      v-else
      xmlns="http://www.w3.org/2000/svg"
      width="28"
      height="28"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  </div>

  <BaseChat
    v-else
    :config="resolvedConfig"
    :chatHistory="chatHistory"
    :isThinking="isThinking"
    :isWidget="isWidget"
    :isSharedView="isSharedView"
    v-model:userMessage="userMessage"
    @sendMessage="sendMessage"
    @reset="resetChat"
    @close="handleClose"
    @share="handleShare"
  />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';

import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import BaseChat from './BaseChat.vue';
import { processBotMessage } from '@/utils/chatProcessor.js';
import { useToast } from '@/composables/useToast';

const { t } = useI18n();

const props = defineProps({
  /** Pass tenantId to fetch config from the public API (standalone page mode) */
  tenantId: { type: String, default: null },
  /** Pass config directly to skip the API fetch (preview mode — live reactive updates) */
  config: { type: Object, default: null },
  isWidget: { type: Boolean, default: false },
  /** When set, loads a read-only shared conversation snapshot */
  shareId: { type: String, default: null },
});

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// ── Config resolution ──────────────────────────────────────────────────────────
const fetchedConfig  = ref(null);
const isSharedView   = ref(false);
const resolvedConfig = computed(() => props.config ?? fetchedConfig.value ?? {});

// Launcher button background — resolved from the config color palette
const launcherBgColor = computed(() => {
  const styles  = resolvedConfig.value.component_styles || {};
  const palette = resolvedConfig.value.color_palette    || [];
  const colorId = styles.launcher_background_color;
  return palette.find(c => c.id === colorId)?.value || colorId || '#A855F7';
});

const { addToast } = useToast();

// ── Open / close state ────────────────────────────────────────────────────────
const emit = defineEmits(['close']);

const isChatOpen = ref(true);

const handleClose = () => {
  if (props.isWidget) {
    // Tell widget.js to hide the iframe; the launcher re-opens it
    window.parent.postMessage({ type: 'burncodes:close-widget' }, '*');
  } else {
    // Show own launcher again and notify any parent that wraps us
    isChatOpen.value = false;
  }
  emit('close');
};

// ── Share ─────────────────────────────────────────────────────────────

const handleShare = async () => {
  if (!props.tenantId) return;
  try {
    const { data } = await axios.post(
      `${API_BASE_URL}/chat/${props.tenantId}/conversation/${conversationId.value}/share`
    );
    const shareUrl = `${window.location.origin}/share/${data.share_id}`;
    await navigator.clipboard.writeText(shareUrl);
    addToast(t('chat.shareCopied'), 'success');
  } catch {
    addToast(t('chat.shareError'), 'error');
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

// ── Shared conversation ───────────────────────────────────────────────────────

const buildSharedHistory = (messages) =>
  messages.flatMap((m) => {
    const entries = [];
    if (m.user_message) entries.push({ text: m.user_message, isUser: true });
    if (m.ai_message) {
      const { text, html } = processBotMessage(m.ai_message);
      entries.push({ text, html, isUser: false });
    }
    return entries;
  });

const fetchSharedConversation = async () => {
  try {
    const { data } = await axios.get(`${API_BASE_URL}/chat/shared/${props.shareId}`);
    chatHistory.value = buildSharedHistory(data.messages || []);
    const cfg = data.widget_config || {};
    cfg.show_share_button = false;
    fetchedConfig.value = cfg;
    isSharedView.value = true;
  } catch (err) {
    const status = err.response?.status;
    const msg = status === 410 ? t('chat.sharedExpired') : t('chat.sharedNotFound');
    const { text, html } = processBotMessage(msg);
    chatHistory.value = [{ text, html, isUser: false }];
  }
};

// ── Lifecycle ─────────────────────────────────────────────────────────────────

// JS-calculated viewport height — avoids 100dvh bugs on mobile browsers
// where the address bar appearing / disappearing causes layout jumps.
// Sets --app-height on the widget root so CSS can consume it.
const widgetRoot = ref(null);

const setAppHeight = () => {
  const h = window.visualViewport ? window.visualViewport.height : window.innerHeight;
  document.documentElement.style.setProperty('--app-height', `${h}px`);
};

onMounted(async () => {
  setAppHeight();
  window.addEventListener('resize', setAppHeight);
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', setAppHeight);
  }

  if (props.shareId) {
    await fetchSharedConversation();
    return;
  }

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
  window.removeEventListener('resize', setAppHeight);
  if (window.visualViewport) {
    window.visualViewport.removeEventListener('resize', setAppHeight);
  }
  if (activeAbortController.value) {
    activeAbortController.value.abort();
    activeAbortController.value = null;
  }
});

</script>

<style scoped>
.chat-launcher {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.20);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  flex-shrink: 0;
}

.chat-launcher:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.28);
}

.chat-launcher:active {
  transform: scale(0.96);
}

.chat-launcher__icon {
  width: 30px;
  height: 30px;
  object-fit: contain;
}
</style>
