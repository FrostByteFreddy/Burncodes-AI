<template>
  <!-- Switched off by the owner: no chat at all -->
  <div v-if="switchedOff" class="chat-off" role="status">
    <p>{{ $t('chat.switchedOff') }}</p>
  </div>

  <!-- Still in development: ask for the password first -->
  <form v-else-if="needsPassword" class="chat-lock" @submit.prevent="unlock">
    <div class="chat-lock__card">
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
      <h1>{{ $t('chat.locked.title') }}</h1>
      <p>{{ $t('chat.locked.body') }}</p>
      <label for="chat-lock-pw" class="chat-lock__label">{{ $t('chat.locked.password') }}</label>
      <input id="chat-lock-pw" v-model="password" type="password" autocomplete="current-password" class="chat-lock__input" autofocus />
      <p v-if="unlockError" class="chat-lock__error" role="alert">{{ unlockError }}</p>
      <button type="submit" class="chat-lock__btn" :disabled="!password || unlocking">{{ $t('chat.locked.open') }}</button>
    </div>
  </form>

  <!-- Collapsed state (non-widget mode only — in widget mode the parent hides the iframe) -->
  <div
    v-else-if="!isChatOpen"
    class="chat-launcher"
    :style="{ backgroundColor: launcherBgColor }"
    @click="isChatOpen = true"
    :title="resolvedConfig.chatbot_title || 'Chat'"
  >
    <img
      v-if="resolvedConfig.launcher_icon"
      :src="resolvedConfig.launcher_icon"
      class="chat-launcher__icon"
      :alt="$t('chat.openChat')"
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
    :calendarFeeds="calendarFeeds"
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
import { supabase } from '@/supabase';
import { processBotMessage } from '@/utils/chatProcessor.js';
import { useToast } from '@/composables/useToast';
import { useAppHeight } from '@/composables/useAppHeight';

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

// The dashboard preview (config passed in) sends the owner's token, so it
// keeps working while the chatbot is switched off for everyone else
const previewAuthHeaders = async () => {
  if (!props.config) return {};
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
};

// ── Password (chatbot still in development) ───────────────────────────────────
// The token from /unlock is kept per chatbot; the server checks it on every message
const accessKey = computed(() => `burncodes-chat-access:${props.tenantId}`);
const readAccess = () => { try { return localStorage.getItem(accessKey.value) || ''; } catch { return ''; } };
const writeAccess = (token) => {
  try { token ? localStorage.setItem(accessKey.value, token) : localStorage.removeItem(accessKey.value); } catch { /* private mode */ }
};
const needsPassword = ref(false);
const password = ref('');
const unlocking = ref(false);
const unlockError = ref('');

const chatHeaders = async () => {
  const access = readAccess();
  return { ...(await previewAuthHeaders()), ...(access ? { 'X-Chat-Access': access } : {}) };
};

// The server says the password is missing or no longer valid: ask again
const isPasswordError = (err) => err.response?.status === 401 && err.response?.data?.code === 'password_required';
const askForPassword = () => { writeAccess(''); needsPassword.value = true; isThinking.value = false; };

const unlock = async () => {
  if (!password.value || unlocking.value) return;
  unlocking.value = true;
  unlockError.value = '';
  try {
    const { data } = await axios.post(`${API_BASE_URL}/chat/${props.tenantId}/unlock`, { password: password.value });
    writeAccess(data.token || '');
    needsPassword.value = false;
    password.value = '';
    await startConversation();
  } catch (err) {
    unlockError.value = err.response?.status === 429 ? t('chat.errors.rateLimited') : t('chat.locked.wrong');
  } finally { unlocking.value = false; }
};

// ── Calendars residents can subscribe to (key → feed) ─────────────────────────
const calendarFeeds = ref({});
const fetchCalendars = async () => {
  if (!props.tenantId) return;
  try {
    const { data } = await axios.get(`${API_BASE_URL}/calendar/${props.tenantId}`);
    calendarFeeds.value = Object.fromEntries((data.feeds || []).map((f) => [f.key, f]));
  } catch { /* no calendar buttons then */ }
};

// ── Config resolution ──────────────────────────────────────────────────────────
const fetchedConfig  = ref(null);
const switchedOff    = ref(false);
const isSharedView   = ref(false);
const resolvedConfig = computed(() => props.config ?? fetchedConfig.value ?? {});

// Launcher button background — resolved from the config color palette
const launcherBgColor = computed(() => {
  const styles  = resolvedConfig.value.component_styles || {};
  const palette = resolvedConfig.value.color_palette    || [];
  const colorId = styles.launcher_background_color;
  return palette.find(c => c.id === colorId)?.value || colorId || '#0A1FAB';
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
    if (data.is_active === false) { switchedOff.value = true; return; }
    fetchedConfig.value = data.widget_config || {};
    if (data.protected && !readAccess()) needsPassword.value = true;
  } catch (err) {
    console.error('[ChatWidget] Failed to fetch tenant config', err);
  }
};

// ── Intro message ─────────────────────────────────────────────────────────────
const fetchIntroMessage = async () => {
  if (!props.tenantId) return;
  isThinking.value = true;
  try {
    const { data } = await axios.get(`${API_BASE_URL}/chat/${props.tenantId}/intro`, { headers: await chatHeaders() });
    const { text, html } = processBotMessage(data.intro_message);
    chatHistory.value.push({ text, html, isUser: false });
    saveSession(chatHistory.value, conversationId.value);
  } catch (err) {
    if (isPasswordError(err)) { askForPassword(); return; }
    const { text, html } = processBotMessage(t('chat.errors.initialMessage'));
    chatHistory.value.push({ text, html, isUser: false });
    saveSession(chatHistory.value, conversationId.value);
  } finally {
    isThinking.value = false;
  }
};

// ── Task polling ──────────────────────────────────────────────────────────────
const pollTaskStatus = (taskId) => {
  // Give up after two minutes; the server may answer immediately instead of
  // holding the request when it is busy, so pace those polls ourselves
  const giveUpAt = Date.now() + 120000;

  const longPoll = async () => {
    if (Date.now() > giveUpAt) {
      isThinking.value = false;
      const { text, html } = processBotMessage(t('chat.errors.taskStatus'));
      chatHistory.value.push({ text, html, isUser: false });
      saveSession(chatHistory.value, conversationId.value);
      return;
    }
    const startedAt = Date.now();
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

        // The backend keeps the conversation server-side; we only append the
        // new answer to the local transcript (which already has the user turn).
        const answer = task_result.answer || '';
        chatHistory.value.push({ text: '', html: '', isUser: false });

        const current = chatHistory.value[chatHistory.value.length - 1];
        for (const part of answer.split(/(\s+)/)) {
          current.text += part;
          current.html = processBotMessage(current.text).html;
          await new Promise(r => setTimeout(r, Math.random() * 5));
        }
        current.calendars = processBotMessage(current.text).calendars;
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

      if (Date.now() - startedAt < 1500) await new Promise((r) => setTimeout(r, 1500));
      await longPoll();
    } catch (err) {
      if (axios.isCancel(err)) return;
      activeAbortController.value = null;
      const { text, html } = processBotMessage(t(err.response?.status === 429 ? 'chat.errors.rateLimited' : 'chat.errors.taskStatus'));
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
  chatHistory.value.push({ text: current, html: null, isUser: true });
  saveSession(chatHistory.value, conversationId.value);
  userMessage.value = '';
  isThinking.value = true;

  try {
    const { data } = await axios.post(`${API_BASE_URL}/chat/${props.tenantId}`, {
      query: current,
      conversation_id: conversationId.value,
    }, { headers: await chatHeaders() });
    if (data.task_id) {
      pollTaskStatus(data.task_id);
    } else {
      throw new Error('No task_id received');
    }
  } catch (err) {
    if (isPasswordError(err)) {
      chatHistory.value.pop();
      userMessage.value = current;
      askForPassword();
      return;
    }
    const code = err.response?.data?.code;
    const { text, html } = processBotMessage(code === 'chatbot_off'
      ? t('chat.switchedOff')
      : err.response?.status === 429
      ? t('chat.errors.rateLimited')
      : t('chat.errors.sendMessage'));
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
      entries.push({ text, html, isUser: false });  // shared snapshots show no calendar buttons
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

useAppHeight();

const widgetRoot = ref(null);

onMounted(async () => {
  if (props.shareId) {
    await fetchSharedConversation();
    return;
  }

  await fetchConfig();
  fetchCalendars();
  if (!needsPassword.value) await startConversation();
});

// Restores this tab's conversation, or starts a new one with the welcome message
async function startConversation() {
  if (!props.tenantId) return;
  const session = loadSession();
  if (session?.history?.length) {
    chatHistory.value = session.history;
    conversationId.value = session.conversationId || uuidv4();
  } else {
    conversationId.value = uuidv4();
    await fetchIntroMessage();
  }
}

onUnmounted(() => {
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
.chat-off {
  display: flex; align-items: center; justify-content: center;
  height: 100%; min-height: 200px; padding: 24px; text-align: center;
  font-family: var(--font-sans, system-ui, sans-serif); color: #4B5563; background: #F9FAFB;
}
.chat-lock {
  display: flex; align-items: center; justify-content: center;
  height: 100%; min-height: 320px; padding: 24px;
  font-family: var(--font-sans, system-ui, sans-serif); background: #F9FAFB; color: #1F2937;
}
.chat-lock__card { width: 100%; max-width: 320px; display: flex; flex-direction: column; gap: 10px; text-align: left; }
.chat-lock__card svg { color: #6B7280; }
.chat-lock__card h1 { font-size: 18px; font-weight: 700; margin: 0; color: #111827; }
.chat-lock__card p { font-size: 14px; color: #4B5563; margin: 0; line-height: 1.45; }
.chat-lock__label { font-size: 14px; font-weight: 600; margin-top: 6px; }
.chat-lock__input { padding: 10px 12px; border: 1px solid #D1D5DB; border-radius: 8px; font-size: 16px; background: #fff; color: #111827; }
.chat-lock__input:focus { outline: 2px solid #0A1FAB; outline-offset: 1px; }
.chat-lock__error { color: #B91C1C !important; }
.chat-lock__btn { padding: 10px 14px; border: none; border-radius: 8px; background: #1F2937; color: #fff; font-size: 15px; font-weight: 600; cursor: pointer; }
.chat-lock__btn:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
