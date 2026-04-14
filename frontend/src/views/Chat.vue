<template>
  <div
    v-if="!isWidget"
    id="test-chat"
    class="bg-base-200 text-base-content font-sans flex items-center justify-center sm:p-4 p-2"
  >
    <BaseChat
      v-if="tenant && tenant.widget_config"
      :config="tenant.widget_config"
      :chatHistory="chatHistory"
      :isThinking="isThinking"
      :isWidget="isWidget"
      v-model:userMessage="userMessage"
      @sendMessage="sendMessage"
      @reset="resetChat"
    />
  </div>
  <BaseChat
    v-else-if="tenant && tenant.widget_config"
    :config="tenant.widget_config"
    :chatHistory="chatHistory"
    :isThinking="isThinking"
    :isWidget="isWidget"
    v-model:userMessage="userMessage"
    @sendMessage="sendMessage"
    @reset="resetChat"
  />
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";
import { processBotMessage } from "@/utils/chatProcessor.js";
import { v4 as uuidv4 } from "uuid";
import BaseChat from "@/components/chat/BaseChat.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

const route = useRoute();
const tenantId = ref(route.params.tenantId);
const tenant = ref(null);
const chatHistory = ref([]);
const userMessage = ref("");
const isThinking = ref(false);
const chatContainer = ref(null);
const conversationId = ref(uuidv4());
const isWidget = ref("widget" in route.query);

// --- Session Storage for Chat History ---
const STORAGE_KEY = `chatSession_${tenantId.value}`;

const saveChatSession = (history, convId) => {
  if (!history || history.length === 0) {
    sessionStorage.removeItem(STORAGE_KEY);
    return;
  }
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ history, conversationId: convId }));
  } catch (e) {
    console.warn("Failed to save chat session:", e);
  }
};

const loadChatSession = () => {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    console.warn("Failed to load chat session:", e);
    return null;
  }
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const fetchTenant = async () => {
  if (!tenantId.value) return;
  try {
    const response = await axios.get(
      `${API_BASE_URL}/tenants/${tenantId.value}/public`
    );
    tenant.value = response.data;
  } catch (error) {
    console.error("Failed to fetch tenant config", error);
  }
};

const fetchIntroMessage = async () => {
  if (!tenantId.value) return;
  isThinking.value = true;
  await scrollToBottom();
  try {
    const response = await axios.get(
      `${API_BASE_URL}/chat/${tenantId.value}/intro`
    );
    const { text, html } = processBotMessage(response.data.intro_message);
    chatHistory.value.push({ text, html, isUser: false });
    saveChatSession(chatHistory.value, conversationId.value);
  } catch (error) {
    const errorMsg = `Error: ${
      error.response?.data?.error || t("chat.errors.initialMessage")
    }`;
    const { text, html } = processBotMessage(errorMsg);
    chatHistory.value.push({ text, html, isUser: false });
    saveChatSession(chatHistory.value, conversationId.value);
  } finally {
    isThinking.value = false;
    await scrollToBottom();
  }
};

const activeAbortController = ref(null);

const pollTaskStatus = (taskId) => {
  let retries = 0;
  const MAX_RETRIES = 4; // 4 × 25s = ~2 minutes max

  const longPoll = async () => {
    if (retries >= MAX_RETRIES) {
      isThinking.value = false;
      const { text, html } = processBotMessage(t("chat.errors.taskStatus"));
      chatHistory.value.push({ text, html, isUser: false });
      saveChatSession(chatHistory.value, conversationId.value);
      await scrollToBottom();
      return;
    }

    retries++;
    const controller = new AbortController();
    activeAbortController.value = controller;

    try {
      const response = await axios.get(
        `${API_BASE_URL}/chat/task/${taskId}/status?timeout=25`,
        { signal: controller.signal, timeout: 30000 }
      );
      const { state: task_status, result: task_result } = response.data;

      if (task_status === "SUCCESS") {
        activeAbortController.value = null;
        isThinking.value = false;
        await scrollToBottom();

        const fullHistory = task_result.chat_history;
        const lastMessageFromServer = fullHistory[fullHistory.length - 1];

        if (lastMessageFromServer && lastMessageFromServer.type === "ai") {
          const previousHistory = fullHistory.slice(0, -1);
          chatHistory.value = previousHistory.map((msg) => {
            if (msg.type === "ai") {
              const { text, html } = processBotMessage(msg.content);
              return { text, html, isUser: false };
            }
            return { text: msg.content, html: null, isUser: true };
          });

          chatHistory.value.push({ text: "", html: "", isUser: false });
          await nextTick();

          const fullBotResponseText = lastMessageFromServer.content;
          const wordsAndSpaces = fullBotResponseText.split(/(\s+)/);
          const currentBotMessage =
            chatHistory.value[chatHistory.value.length - 1];

          for (const part of wordsAndSpaces) {
            currentBotMessage.text += part;
            currentBotMessage.html = processBotMessage(
              currentBotMessage.text
            ).html;

            await scrollToBottom();

            const delay = Math.random() * (10 - 5);
            await new Promise((resolve) => setTimeout(resolve, delay));
          }
          saveChatSession(chatHistory.value, conversationId.value);
        } else {
          chatHistory.value = fullHistory.map((msg) => {
            if (msg.type === "ai") {
              const { text, html } = processBotMessage(msg.content);
              return { text, html, isUser: false };
            }
            return { text: msg.content, html: null, isUser: true };
          });
          saveChatSession(chatHistory.value, conversationId.value);
          await scrollToBottom();
        }
        return;
      } else if (task_status === "FAILURE") {
        activeAbortController.value = null;
        const errorMsg = `${t("chat.errors.processingFailed")} ${
          task_result?.exc_message || ""
        }`;
        const { text, html } = processBotMessage(errorMsg);
        chatHistory.value.push({ text, html, isUser: false });
        saveChatSession(chatHistory.value, conversationId.value);
        isThinking.value = false;
        await scrollToBottom();
        return;
      }

      // Still pending after timeout — retry long poll
      await longPoll();
    } catch (error) {
      if (axios.isCancel(error)) return; // Component unmounted
      activeAbortController.value = null;
      const errorMsg = t("chat.errors.taskStatus");
      const { text, html } = processBotMessage(errorMsg);
      chatHistory.value.push({ text, html, isUser: false });
      saveChatSession(chatHistory.value, conversationId.value);
      isThinking.value = false;
      await scrollToBottom();
    }
  };

  longPoll();
};

onUnmounted(() => {
  if (activeAbortController.value) {
    activeAbortController.value.abort();
    activeAbortController.value = null;
  }
});

const sendMessage = async () => {
  if (!userMessage.value.trim() || !tenantId.value || isThinking.value) return;

  const currentMessage = userMessage.value;
  const historyForBackend = chatHistory.value.map((msg) => ({
    type: msg.isUser ? "human" : "ai",
    content: msg.text,
  }));

  chatHistory.value.push({ text: currentMessage, html: null, isUser: true });
  saveChatSession(chatHistory.value, conversationId.value);
  userMessage.value = "";
  isThinking.value = true;
  await scrollToBottom();

  try {
    const payload = {
      query: currentMessage,
      chat_history: historyForBackend,
      conversation_id: conversationId.value,
    };
    const response = await axios.post(
      `${API_BASE_URL}/chat/${tenantId.value}`,
      payload
    );
    const { task_id } = response.data;
    if (task_id) {
      pollTaskStatus(task_id);
    } else {
      throw new Error("No task_id received from the server.");
    }
  } catch (error) {
    const errorMsg = `Error: ${
      error.response?.data?.error || t("chat.errors.sendMessage")
    }`;
    const { text, html } = processBotMessage(errorMsg);
    chatHistory.value.push({ text, html, isUser: false });
    saveChatSession(chatHistory.value, conversationId.value);
    isThinking.value = false;
    await scrollToBottom();
  }
};

const resetChat = () => {
  chatHistory.value = [];
  conversationId.value = uuidv4();
  saveChatSession([], null);
  fetchIntroMessage();
};

onMounted(async () => {
  await fetchTenant();
  const sessionData = loadChatSession();
  if (sessionData && sessionData.history && sessionData.history.length > 0) {
    chatHistory.value = sessionData.history;
    conversationId.value = sessionData.conversationId || uuidv4();
    scrollToBottom();
  } else {
    conversationId.value = uuidv4();
    fetchIntroMessage();
  }

  if (chatContainer.value) {
    chatContainer.value.addEventListener("click", (e) => {
      const link = e.target.closest("a");
      if (link && link.href && link.hostname !== window.location.hostname) {
        e.preventDefault();
        window.open(link.href, "_blank", "noopener,noreferrer");
      }
    });
  }
});
</script>

<style scoped>
/* All styles are now in BaseChat.vue */
</style>
